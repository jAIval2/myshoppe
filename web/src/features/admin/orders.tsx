"use client";
import { ErrorMessage } from "@/components/ui";
import { api, json, money, type Order } from "@/lib/api";
import Link from "next/link";
import { useEffect, useState } from "react";

export function AdminOrders() {
  const [data, setData] = useState<Order[]>([]);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    api<Order[]>("/admin/orders").then(setData).catch(setError);
  }, []);
  return (
    <>
      <div className="admin-title">
        <h1>Orders</h1>
        <span>{data.length} RECENT ORDERS</span>
      </div>
      <ErrorMessage error={error} />
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ORDER</th>
              <th>CUSTOMER</th>
              <th>PAYMENT</th>
              <th>FULFILMENT</th>
              <th>TOTAL</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.map((o) => (
              <tr key={o.id}>
                <td>
                  MS{o.number}
                  <small>{o.payment_mode}</small>
                </td>
                <td>
                  {o.address.name}
                  <small>{o.address.email}</small>
                </td>
                <td>{o.status}</td>
                <td>{o.fulfilment}</td>
                <td>{money(o.total)}</td>
                <td>
                  <Link href={`/admin/orders/${o.id}`}>OPEN →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export function AdminOrder({ id }: { id: string }) {
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [tracking, setTracking] = useState("");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const load = () => api<Order>(`/admin/orders/${id}`).then(setOrder);
  useEffect(() => {
    load().catch(setError);
  }, [id]);
  async function action(path: string, body: unknown) {
    setBusy(true);
    setError(null);
    try {
      await api(path, json("POST", body));
      await load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Link href="/admin/orders">← ORDERS</Link>
      <ErrorMessage error={error} />
      {order && (
        <>
          <div className="admin-title">
            <h1>Order MS{order.number}</h1>
            <span className="status">
              {order.status} / {order.fulfilment}
            </span>
          </div>
          <div className="editor-grid">
            <section className="admin-panel">
              <h2>Items</h2>
              {order.items.map((i) => (
                <div className="shipment-line" key={i.id}>
                  <img src={i.snapshot.image} alt="" />
                  <div>
                    <p>{i.snapshot.title}</p>
                    <p>
                      {i.snapshot.size} / {i.snapshot.colour}
                    </p>
                    <small>
                      Ordered {i.quantity} · Shipped {i.shipped} · Returned{" "}
                      {i.returned}
                    </small>
                  </div>
                  <input
                    aria-label={`Ship quantity for ${i.snapshot.title}`}
                    type="number"
                    min="0"
                    max={i.quantity - i.shipped}
                    value={quantities[i.id] || 0}
                    onChange={(e) =>
                      setQuantities({
                        ...quantities,
                        [i.id]: Number(e.target.value),
                      })
                    }
                  />
                </div>
              ))}
              <label className="field">
                Carrier / tracking reference
                <input
                  value={tracking}
                  onChange={(e) => setTracking(e.target.value)}
                />
              </label>
              <button
                className="button"
                disabled={busy || order.status !== "paid"}
                onClick={() =>
                  action(`/admin/orders/${id}/shipments`, {
                    tracking,
                    items: Object.fromEntries(
                      Object.entries(quantities).filter(([, q]) => q > 0),
                    ),
                  })
                }
              >
                CREATE SHIPMENT
              </button>
              <button
                className="button"
                disabled={busy || order.fulfilment !== "shipped"}
                onClick={() => action(`/admin/orders/${id}/delivered`, {})}
              >
                MARK DELIVERED
              </button>
            </section>
            <section className="admin-panel">
              <h2>Customer</h2>
              <p>
                {order.address.name}
                <br />
                {order.address.email}
                <br />
                {order.address.phone}
              </p>
              <p>
                {order.address.line1}
                <br />
                {order.address.city}, {order.address.state} {order.address.pin}
              </p>
              <hr />
              <h2>Payment</h2>
              <p>
                {money(order.total)} / {order.payment_mode.toUpperCase()}
              </p>
              <label className="field">
                Refund amount (₹)
                <input
                  type="number"
                  min="1"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </label>
              <label className="field">
                Reason
                <input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
              <button
                className="button"
                disabled={busy}
                onClick={() => {
                  if (
                    confirm(
                      `Request a refund of ${money(Math.round(Number(amount) * 100))}?`,
                    )
                  )
                    action(`/admin/orders/${id}/refunds`, {
                      amount: Math.round(Number(amount) * 100),
                      reason,
                      request_key: crypto.randomUUID(),
                    });
                }}
              >
                REQUEST REFUND
              </button>
              {order.refunds.map((r) => (
                <p key={r.id}>
                  {money(r.amount)} / {r.status}
                </p>
              ))}
            </section>
          </div>
          {order.returns.length > 0 && (
            <section className="admin-panel">
              <h2>Returns</h2>
              {order.returns.map((r) => (
                <div className="return-row" key={r.id}>
                  <span>
                    {r.reason} / {r.status}
                  </span>
                  {r.status === "requested" && (
                    <>
                      <button
                        className="button"
                        disabled={busy}
                        onClick={() =>
                          action(`/admin/returns/${r.id}/receive`, {
                            sellable: true,
                          })
                        }
                      >
                        RECEIVED, SELLABLE
                      </button>
                      <button
                        className="button"
                        disabled={busy}
                        onClick={() =>
                          action(`/admin/returns/${r.id}/receive`, {
                            sellable: false,
                          })
                        }
                      >
                        RECEIVED, QUARANTINE
                      </button>
                    </>
                  )}
                </div>
              ))}
            </section>
          )}
        </>
      )}
    </>
  );
}
