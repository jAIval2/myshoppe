import json
import os
from pathlib import Path
import httpx
from app.settings import settings
from app.errors import require


def send_order(order):
    message = {
        "to": [order["address"]["email"]],
        "subject": f"MyShoppe order MS{order['number']}",
        "text": f"Your order MS{order['number']} is confirmed. Total INR {order['total'] / 100:.2f}. Follow your order at {settings.origin}/account/orders/{order['id']}.",
    }
    if order["payment_mode"] == "development":
        require(settings.environment == "development", "INVALID_MODE", "Development email forbidden")
        folder = Path(__file__).resolve().parents[3] / ".local/mail"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{order['id']}.json").write_text(json.dumps({**message, "development_only": True}))
        return
    key, sender = os.getenv("RESEND_API_KEY"), os.getenv("EMAIL_FROM")
    require(key and sender, "EMAIL_UNCONFIGURED", "Email provider is not configured", 503)
    with httpx.Client(timeout=15) as client:
        result = client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Idempotency-Key": f"order-{order['id']}"},
            json={**message, "from": sender},
        )
        result.raise_for_status()
