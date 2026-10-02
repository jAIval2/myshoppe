"use client";
import { ErrorMessage } from "@/components/ui";
import { api, json, money } from "@/lib/api";
import Link from "next/link";
import { useEffect, useState } from "react";

type Dashboard = {
  paused: boolean;
  captured: number;
  refunded: number;
  net: number;
  orders: number;
  low_stock: number;
  exceptions: {
    id: string;
    kind: string;
    status: string;
    last_error: string;
  }[];
  audit: { id: string; action: string; created_at: string }[];
};
export function AdminOverview() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    api<Dashboard>("/admin/dashboard")
      .then((value) => {
        setData(value);
        setPaused(value.paused);
      })
      .catch(setError);
  }, []);
  return (
    <>
      <div className="admin-title">
        <div>
          <p className="eyebrow">YOUR BOUTIQUE, AT A GLANCE</p>
          <h1>Overview</h1>
        </div>
        <Link className="button primary" href="/admin/products/new">
          ADD PRODUCT
        </Link>
      </div>
      <ErrorMessage error={error} />
      {data && (
        <>
          <div className="metric-grid">
            {[
              ["Net captured", money(data.net)],
              ["Orders", data.orders],
              ["Refunded", money(data.refunded)],
              ["Low-stock variants", data.low_stock],
            ].map(([label, value]) => (
              <div className="metric" key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
                <small>ALL TIME · DEVELOPMENT & LIVE SEPARATED ON ORDERS</small>
              </div>
            ))}
          </div>
          <section className="admin-section">
            <h2>Needs attention</h2>
            {data.exceptions.length ? (
              data.exceptions.map((j) => (
                <div className="exception" key={j.id}>
                  <strong>
                    {j.kind} / {j.status}
                  </strong>
                  <p>{j.last_error}</p>
                  {j.status === "failed" && (
                    <button
                      className="button"
                      onClick={async () => {
                        try {
                          await api(`/admin/jobs/${j.id}/retry`, json("POST"));
                          setData(await api<Dashboard>("/admin/dashboard"));
                        } catch (e) {
                          setError(e);
                        }
                      }}
                    >
                      RETRY RECOVERY
                    </button>
                  )}
                </div>
              ))
            ) : (
              <p className="muted">No failed jobs or payment exceptions.</p>
            )}
          </section>
          <section className="admin-section">
            <h2>Recent activity</h2>
            {data.audit.map((a) => (
              <div className="audit-row" key={a.id}>
                <span>{a.action.replaceAll(".", " / ")}</span>
                <time>{new Date(a.created_at).toLocaleString("en-IN")}</time>
              </div>
            ))}
          </section>
          <button
            className="button"
            onClick={async () => {
              try {
                await api(
                  "/admin/checkout-pause",
                  json("POST", { paused: !paused }),
                );
                setPaused(!paused);
              } catch (e) {
                setError(e);
              }
            }}
          >
            {paused ? "RESUME CHECKOUT" : "PAUSE NEW CHECKOUTS"}
          </button>
        </>
      )}
    </>
  );
}
