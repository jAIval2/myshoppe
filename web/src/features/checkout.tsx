"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, json, money, type Address, type Order } from "@/lib/api";
import { useShop } from "@/components/shop-provider";
import { ErrorMessage } from "@/components/ui";

type Quote = {
  subtotal: number;
  shipping: number;
  total: number;
  quote_hash: string;
  tax_note: string;
  development: boolean;
};
type PaymentSession = {
  mode: string;
  order_id?: string;
  amount: number;
  provider_order_id?: string;
  key?: string;
};
declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => { open: () => void };
  }
}
async function loadPayment() {
  if (window.Razorpay) return;
  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve();
    script.onerror = () =>
      reject(
        new Error(
          "Payment could not load. Your order is available in your account.",
        ),
      );
    document.body.appendChild(script);
  });
}

export function CheckoutPage() {
  const shop = useShop();
  const router = useRouter();
  const [quote, setQuote] = useState<Quote | null>(null);
  const [address, setAddress] = useState<Address | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [attempt, setAttempt] = useState<Order | null>(null);
  const [key] = useState(() => crypto.randomUUID());
  async function review(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError(null);
    const data = Object.fromEntries(new FormData(e.currentTarget)) as Address;
    try {
      setQuote(await api<Quote>("/checkout/quote", json("POST", data)));
      setAddress(data);
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  async function pay() {
    if (!quote || !address) return;
    setPending(true);
    setError(null);
    try {
      const order =
        attempt ||
        (await api<Order>(
          "/checkout/attempts",
          json("POST", {
            address,
            quote_hash: quote.quote_hash,
            request_key: key,
          }),
        ));
      setAttempt(order);
      const payment = await api<PaymentSession>(
        "/payments/session",
        json("POST", { order_id: order.id }),
      );
      if (payment.mode === "development") {
        await api(`/payments/development/${order.id}/capture`, json("POST"));
        await shop.refresh();
        router.push(`/account/orders/${order.id}`);
      } else {
        await loadPayment();
        new window.Razorpay({
          key: payment.key,
          order_id: payment.provider_order_id,
          amount: payment.amount,
          currency: "INR",
          name: "MyShoppe",
          description: `Order ${order.number}`,
          prefill: {
            name: address.name,
            email: address.email,
            contact: address.phone,
          },
          handler: () => router.push(`/account/orders/${order.id}`),
          modal: {
            ondismiss: () => router.push(`/account/orders/${order.id}`),
          },
        }).open();
      }
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  return (
    <main id="main" className="checkout-page">
      <Link className="text-link" href="/cart">
        ← BACK TO BAG
      </Link>
      <h1>{quote ? "REVIEW YOUR ORDER" : "YOUR DETAILS"}</h1>
      <div className="checkout-layout">
        <section>
          <ErrorMessage error={error} />
          {!quote ? (
            <form onSubmit={review} className="address-form">
              {[
                ["name", "Full name", "text"],
                ["email", "Email address", "email"],
                ["phone", "Mobile number", "tel"],
                ["line1", "Address", "text"],
                ["city", "City", "text"],
                ["state", "State", "text"],
                ["pin", "PIN code", "text"],
              ].map(([name, label, type]) => (
                <label className="field" key={name}>
                  {label}
                  <input
                    name={name}
                    type={type}
                    required
                    autoComplete={
                      {
                        name: "name",
                        email: "email",
                        phone: "tel-national",
                        line1: "address-line1",
                        city: "address-level2",
                        state: "address-level1",
                        pin: "postal-code",
                      }[name]
                    }
                    pattern={
                      name === "phone"
                        ? "[6-9][0-9]{9}"
                        : name === "pin"
                          ? "[1-9][0-9]{5}"
                          : undefined
                    }
                  />
                </label>
              ))}
              <p className="micro">INDIA / INR</p>
              <button
                className="button primary"
                disabled={pending || !shop.cart.count}
              >
                {pending ? "CHECKING…" : "CONTINUE TO REVIEW"}
              </button>
            </form>
          ) : (
            <div className="order-review">
              <h2>DELIVERY ADDRESS</h2>
              <p>
                {address?.name}
                <br />
                {address?.line1}
                <br />
                {address?.city}, {address?.state} {address?.pin}
                <br />
                {address?.phone}
              </p>
              <button
                className="text-link"
                disabled={!!attempt}
                onClick={() => setQuote(null)}
              >
                EDIT DETAILS
              </button>
              <hr />
              <h2>DELIVERY</h2>
              <p>
                Standard delivery •{" "}
                {quote.shipping ? money(quote.shipping) : "Complimentary"}
              </p>
              <p className="micro muted">{quote.tax_note}</p>
              {quote.development && (
                <p className="development-note">
                  DEVELOPMENT CHECKOUT
                  <br />
                  No money will be charged. This verifies the order and
                  inventory flow.
                </p>
              )}
              <button
                className="button primary"
                disabled={pending}
                onClick={pay}
              >
                {pending
                  ? "PLEASE WAIT…"
                  : quote.development
                    ? "PLACE DEVELOPMENT ORDER"
                    : `PAY ${money(quote.total)}`}
              </button>
              <p className="micro">
                By placing an order you agree to our{" "}
                <Link href="/help/terms">terms</Link> and{" "}
                <Link href="/help/privacy">privacy policy</Link>.
              </p>
            </div>
          )}
        </section>
        <aside className="order-summary">
          <h2>YOUR BAG ({shop.cart.count})</h2>
          {shop.cart.items.map((i) => (
            <div key={i.variant_id} className="summary-item">
              <img src={i.image} alt={i.title} />
              <div>
                <p>{i.title}</p>
                <p>
                  {i.size} / {i.colour} / QTY {i.quantity}
                </p>
                <p>{money(i.price_paise * i.quantity)}</p>
              </div>
            </div>
          ))}
          <div className="summary-total">
            <span>Subtotal</span>
            <span>{money(quote?.subtotal || shop.cart.subtotal)}</span>
          </div>
          <div className="summary-total">
            <span>Delivery</span>
            <span>
              {quote
                ? quote.shipping
                  ? money(quote.shipping)
                  : "Complimentary"
                : "Calculated next"}
            </span>
          </div>
          <div className="summary-total final">
            <span>TOTAL</span>
            <span>{money(quote?.total || shop.cart.subtotal)}</span>
          </div>
        </aside>
      </div>
    </main>
  );
}
