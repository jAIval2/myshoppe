"use client";
import { useShop } from "@/components/shop-provider";
import { Loading } from "@/components/ui";
import Link from "next/link";

export function AdminShell({ children }: { children: React.ReactNode }) {
  const shop = useShop();
  return (
    <div className="admin-shell">
      <header>
        <Link className="admin-wordmark" href="/admin">
          myshoppe<span>ATELIER / ADMINISTRATION</span>
        </Link>
        <Link href="/">VIEW STORE ↗</Link>
        <Link href="/account">{shop.session?.name || "SIGN IN"}</Link>
      </header>
      <aside>
        <Link href="/admin">OVERVIEW</Link>
        <Link href="/admin/products">PRODUCTS & INVENTORY</Link>
        <Link href="/admin/orders">ORDERS</Link>
        <Link href="/admin/content">CAMPAIGNS</Link>
        <Link href="/admin/support">SUPPORT</Link>
        <p>INDIA / INR</p>
      </aside>
      <main id="main">
        {!shop.session ? (
          <Loading />
        ) : !shop.session.role ? (
          <div className="empty-state">
            <h1>Staff access required</h1>
            <p>Sign in with an authorized boutique account.</p>
            <Link className="button" href="/account">
              SIGN IN
            </Link>
          </div>
        ) : (
          children
        )}
      </main>
    </div>
  );
}
