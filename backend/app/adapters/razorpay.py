import hashlib
import hmac
import httpx
from app.errors import require, DomainError
from app.settings import settings


class RazorpayGateway:
    def __init__(self):
        self.client = httpx.Client(
            base_url="https://api.razorpay.com/v1",
            auth=(settings.razorpay_id, settings.razorpay_secret),
            timeout=15,
        )

    def request(self, method, path, **kwargs):
        require(
            settings.razorpay_id and settings.razorpay_secret,
            "PAYMENTS_UNCONFIGURED",
            "Payments are not configured.",
            503,
        )
        try:
            response = self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise DomainError(
                "PROVIDER_UNKNOWN", "Payment provider response is uncertain; reconciliation is required.", 503
            ) from exc

    def create_order(self, order):
        return self.request(
            "POST",
            "/orders",
            json={
                "amount": order["total"],
                "currency": "INR",
                "receipt": str(order["id"]),
                "notes": {"local_order_id": order["id"]},
            },
        )

    def fetch_payment(self, payment_id):
        return self.request("GET", f"/payments/{payment_id}")

    def fetch_order_payments(self, provider_id):
        return self.request("GET", f"/orders/{provider_id}/payments")

    def find_order(self, order):
        matches = []
        # Bounded scan. An exhausted window is an operator exception, never permission to create again.
        for page in range(5):
            rows = self.request(
                "GET",
                "/orders",
                params={
                    "from": int(order["created_at"].timestamp()) - 60,
                    "to": int(order["expires_at"].timestamp()) + 60,
                    "count": 100,
                    "skip": page * 100,
                },
            )["items"]
            matches.extend(r for r in rows if r.get("receipt") == str(order["id"]))
            if len(rows) < 100:
                require(len(matches) <= 1, "MULTIPLE_ORDERS", "Multiple provider orders need review.")
                return matches[0] if matches else None
        raise DomainError(
            "RECONCILE_LIMIT", "Provider search exceeded its bounded window; operator review required.", 503
        )

    def find_refund(self, payment_id, refund_id):
        for page in range(5):
            rows = self.request(
                "GET", f"/payments/{payment_id}/refunds", params={"count": 100, "skip": page * 100}
            )["items"]
            matches = [
                r
                for r in rows
                if isinstance(r.get("notes"), dict) and r["notes"].get("local_refund_id") == refund_id
            ]
            require(len(matches) <= 1, "MULTIPLE_REFUNDS", "Multiple provider refunds need review.")
            if matches:
                return matches[0]
            if len(rows) < 100:
                return None
        raise DomainError("RECONCILE_LIMIT", "Refund search exceeded its bounded window.", 503)

    def refund(self, payment_id, amount, refund_id):
        return self.request(
            "POST",
            f"/payments/{payment_id}/refund",
            json={"amount": amount, "notes": {"local_refund_id": refund_id}},
        )

    def verify(self, raw, signature):
        require(bool(settings.webhook_secret), "PAYMENTS_UNCONFIGURED", "Webhook is not configured.", 503)
        expected = hmac.new(settings.webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
        require(
            hmac.compare_digest(expected, signature), "INVALID_SIGNATURE", "Invalid webhook signature.", 401
        )
