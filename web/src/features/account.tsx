"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, json, money, type Order } from "@/lib/api";
import { useShop } from "@/components/shop-provider";
import { ErrorMessage, Loading } from "@/components/ui";

export function Account() {
  const shop = useShop();
  const [orders, setOrders] = useState<Order[]>([]);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [mfa, setMfa] = useState<{
    access_token: string;
    factor_id: string;
    secret?: string;
    qr_code?: string;
  } | null>(null);
  const [factorCode, setFactorCode] = useState("");
  async function verifyFactor(e: React.FormEvent) {
    e.preventDefault();
    if (!mfa) return;
    setPending(true);
    try {
      await api(
        "/auth/mfa",
        json("POST", {
          access_token: mfa.access_token,
          factor_id: mfa.factor_id,
          code: factorCode,
        }),
      );
      setMfa(null);
      setFactorCode("");
      await shop.refresh();
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  useEffect(() => {
    if (shop.session) api<Order[]>("/orders").then(setOrders).catch(setError);
  }, [shop.session]);
  async function login(development = false, account = email) {
    setPending(true);
    setError(null);
    try {
      const result = await api<{
        mfa_required?: boolean;
        access_token?: string;
      }>(
        development ? "/auth/development" : "/auth/email",
        json("POST", { email: account, ...(code ? { code } : {}) }),
      );
      if (result.mfa_required && result.access_token) {
        const factor = await api<{
          factor_id: string;
          secret?: string;
          qr_code?: string;
        }>("/auth/mfa", json("POST", { access_token: result.access_token }));
        setMfa({ ...factor, access_token: result.access_token });
        return;
      }
      if (development || code) await shop.refresh();
      else setSent(true);
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  return (
    <main id="main" className="account-page">
      <h1>
        {shop.session?.name
          ? `HELLO, ${shop.session.name.toUpperCase()}`
          : "WELCOME TO MYSHOPPE"}
      </h1>
      <ErrorMessage error={error} />
      {!shop.session?.name ? (
        <div className="login-panel">
          <p>Sign in to keep your favourites close and follow your orders.</p>
          {mfa ? (
            <form onSubmit={verifyFactor}>
              <h2>VERIFY YOUR AUTHENTICATOR</h2>
              {mfa.secret && (
                <>
                  <p>
                    Add MyShoppe to your authenticator, then enter its six-digit
                    code.
                  </p>
                  {mfa.qr_code && (
                    <img
                      className="mfa-qr"
                      src={
                        mfa.qr_code.startsWith("data:image/")
                          ? mfa.qr_code
                          : `data:image/svg+xml,${encodeURIComponent(mfa.qr_code)}`
                      }
                      alt="Authenticator enrollment QR code"
                    />
                  )}
                  <label className="field">
                    Setup key
                    <input readOnly value={mfa.secret} />
                  </label>
                </>
              )}
              <label className="field">
                Authenticator code
                <input
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  required
                  value={factorCode}
                  onChange={(e) => setFactorCode(e.target.value)}
                />
              </label>
              <button className="button primary" disabled={pending}>
                VERIFY & SIGN IN
              </button>
              <button
                type="button"
                onClick={() => {
                  setMfa(null);
                  setFactorCode("");
                  setCode("");
                }}
              >
                CANCEL
              </button>
            </form>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                login();
              }}
            >
              <label className="field">
                Email
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              {sent && (
                <label className="field">
                  Email verification code
                  <input
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                  />
                </label>
              )}
              <button className="button primary" disabled={pending}>
                {pending
                  ? "PLEASE WAIT…"
                  : sent
                    ? "SIGN IN"
                    : "EMAIL ME A CODE"}
              </button>
            </form>
          )}
          {shop.session?.development && (
            <details className="development-login">
              <summary>Development accounts</summary>
              <p>
                Local preview only. These accounts do not authenticate real
                customers.
              </p>
              {[
                "customer",
                "owner",
                "merchandiser",
                "fulfilment",
                "support",
              ].map((role) => (
                <button
                  className="button"
                  key={role}
                  disabled={pending}
                  onClick={() => login(true, `${role}@myshoppe.local`)}
                >
                  CONTINUE AS {role.toUpperCase()}
                </button>
              ))}
            </details>
          )}
        </div>
      ) : (
        <div className="account-actions">
          <Link href="/favourites">FAVOURITES</Link>
          {shop.session.role && <Link href="/admin">OPEN BOUTIQUE ADMIN</Link>}
          <button
            onClick={async () => {
              await api("/auth/logout", json("POST"));
              await shop.refresh();
            }}
          >
            LOG OUT
          </button>
        </div>
      )}
      <section className="account-orders">
        <h2>YOUR ORDERS</h2>
        {orders.length ? (
          orders.map((order) => (
            <Link
              className="order-row"
              key={order.id}
              href={`/account/orders/${order.id}`}
            >
              <span>
                MS{order.number}
                <small>
                  {new Date(order.created_at).toLocaleDateString("en-IN")}
                </small>
              </span>
              <span>{order.status.replaceAll("_", " ").toUpperCase()}</span>
              <span>{money(order.total)} →</span>
            </Link>
          ))
        ) : (
          <p className="muted">Your orders will appear here.</p>
        )}
      </section>
    </main>
  );
}

export function OrderDetail({ id }: { id: string }) {
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [pending, setPending] = useState(false);
  const [reason, setReason] = useState("");
  useEffect(() => {
    let alive = true;
    const load = () =>
      api<Order>(`/orders/${id}`)
        .then((d) => {
          if (alive) setOrder(d);
        })
        .catch(setError);
    load();
    const timer = setInterval(load, 5000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [id]);
  async function requestReturn(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!order) return;
    setPending(true);
    try {
      await api(
        `/orders/${id}/returns`,
        json("POST", {
          items: Object.fromEntries(
            order.items
              .filter((i) => i.shipped > i.returned)
              .map((i) => [i.id, i.shipped - i.returned]),
          ),
          reason,
          request_key: crypto.randomUUID(),
        }),
      );
      setOrder(await api<Order>(`/orders/${id}`));
      setReason("");
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  if (!order)
    return (
      <main id="main" className="account-page">
        <ErrorMessage error={error} />
        <Loading label="Loading your order" />
      </main>
    );
  return (
    <main id="main" className="order-page">
      <Link href="/account" className="text-link">
        ← YOUR ORDERS
      </Link>
      <p className="eyebrow">ORDER MS{order.number}</p>
      <h1>
        {order.status === "paid"
          ? "Thank you. It’s yours."
          : order.status === "pending"
            ? "Confirming your payment."
            : order.status.replaceAll("_", " ")}
      </h1>
      {order.payment_mode === "development" && (
        <p className="development-note">
          DEVELOPMENT ORDER — NO PAYMENT WAS CHARGED
        </p>
      )}
      <ErrorMessage error={error} />
      <p className="muted">
        {order.status === "paid"
          ? "Your order is confirmed. Follow its progress here."
          : "Payment status is checked automatically. Closing this page will not lose your order."}
      </p>
      <div className="order-timeline">
        <span className="complete">ORDER RECEIVED</span>
        <span className={order.status === "paid" ? "complete" : ""}>
          PAYMENT CONFIRMED
        </span>
        <span
          className={
            order.fulfilment === "shipped" || order.fulfilment === "delivered"
              ? "complete"
              : ""
          }
        >
          SHIPPED
        </span>
        <span className={order.fulfilment === "delivered" ? "complete" : ""}>
          DELIVERED
        </span>
      </div>
      <div className="order-detail-grid">
        <section>
          {order.items.map((i) => (
            <div className="summary-item" key={i.id}>
              <img src={i.snapshot.image} alt={i.snapshot.title} />
              <div>
                <p>{i.snapshot.title}</p>
                <p>
                  {i.snapshot.size} / {i.snapshot.colour} / QTY {i.quantity}
                </p>
                <p>{money(i.price_paise * i.quantity)}</p>
              </div>
            </div>
          ))}
          <div className="summary-total final">
            <span>TOTAL</span>
            <span>{money(order.total)}</span>
          </div>
        </section>
        <section>
          <h2>DELIVERY ADDRESS</h2>
          <p>
            {order.address.name}
            <br />
            {order.address.line1}
            <br />
            {order.address.city} {order.address.pin}
          </p>
          {order.shipments.map((s) => (
            <p key={s.id}>
              Tracking: {s.tracking} / {s.status}
            </p>
          ))}
          {order.refunds.map((r) => (
            <p key={r.id}>
              Refund {money(r.amount)} — {r.status}
            </p>
          ))}
          {order.returns.map((r) => (
            <p key={r.id}>Return — {r.status}</p>
          ))}
        </section>
      </div>
      {order.fulfilment === "delivered" && !order.returns.length && (
        <form className="return-form" onSubmit={requestReturn}>
          <h2>REQUEST A RETURN</h2>
          <label className="field">
            Tell us why
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              minLength={3}
              required
            />
          </label>
          <button className="button" disabled={pending}>
            REQUEST RETURN
          </button>
        </form>
      )}
      <Link className="button" href="/women">
        CONTINUE EXPLORING
      </Link>
    </main>
  );
}
