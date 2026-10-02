"use client";
import { ErrorMessage } from "@/components/ui";
import { api } from "@/lib/api";
import { useEffect, useState } from "react";

export function AdminSupport() {
  const [data, setData] = useState<
    {
      id: string;
      email: string;
      subject: string;
      message: string;
      status: string;
    }[]
  >([]);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    api<typeof data>("/admin/support").then(setData).catch(setError);
  }, []);
  return (
    <>
      <h1>Support inbox</h1>
      <ErrorMessage error={error} />
      {data.map((t) => (
        <section className="admin-panel" key={t.id}>
          <h2>{t.subject}</h2>
          <p>
            {t.email} / {t.status}
          </p>
          <p>{t.message}</p>
        </section>
      ))}
      {!data.length && <p className="muted">No customer requests yet.</p>}
    </>
  );
}
