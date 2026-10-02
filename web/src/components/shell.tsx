"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { categories, titleCase, type Department } from "@/lib/api";
import { useShop } from "./shop-provider";
import { Dialog } from "./ui";

export function Shell() {
  const path = usePathname();
  const shop = useShop();
  const [open, setOpen] = useState(false);
  const [department, setDepartment] = useState<Department>("women");
  useEffect(() => {
    setOpen(false);
  }, [path]);
  if (path.startsWith("/admin")) return null;
  const clean = path.startsWith("/checkout");
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className={`corner-controls ${clean ? "checkout-header" : ""}`}>
        <button
          className={`menu-trigger ${open ? "is-open" : ""}`}
          aria-label="Open menu"
          aria-expanded={open}
          onClick={() => setOpen(true)}
        >
          <span />
          <span />
        </button>
        <Link className="compact-wordmark" href="/">
          myshoppe
        </Link>
        <Link className="search-trigger" href="/search">
          SEARCH
        </Link>
        <Link
          className="mobile-bag"
          href="/cart"
          aria-label={`Bag, ${shop.cart.count} items`}
        >
          BAG [{shop.cart.count}]
        </Link>
      </header>
      {!clean && (
        <nav className="utility-rail" aria-label="Account and shopping">
          <Link href="/cart" className={path === "/cart" ? "active" : ""}>
            BAG <span className="bag-number">{shop.cart.count}</span>
          </Link>
          {path === "/cart" && <Link href="/favourites">FAVOURITES</Link>}
          <Link href="/account">
            {shop.session?.name ? "ACCOUNT" : "LOG IN"}
          </Link>
          <Link href="/help">HELP</Link>
        </nav>
      )}
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Navigation"
        className="navigation-dialog"
      >
        <Link className="menu-wordmark" href="/" onClick={() => setOpen(false)}>
          myshoppe
        </Link>
        <div className="menu-columns">
          <div className="departments">
            {(["women", "home"] as Department[]).map((d) => (
              <button
                key={d}
                aria-pressed={department === d}
                onClick={() => setDepartment(d)}
              >
                {department === d && <span className="department-dot">•</span>}
                {d.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="menu-groups">
            <div className="menu-group">
              <span>|01| NEW IN</span>
              <div>
                <Link href={`/collections/${department}-new-in`}>THE NEW</Link>
                <Link href={`/collections/${department}-new-in?view=1`}>
                  THE OCTOBER EDIT
                </Link>
                <Link href={`/collections/${department}-new-in?view=2`}>
                  CONSIDERED ESSENTIALS
                </Link>
              </div>
            </div>
            <div className="menu-group">
              <span>|02| COLLECTION</span>
              <div>
                <Link href={`/${department}`}>VIEW ALL</Link>
                {categories[department].map((c) => (
                  <Link key={c} href={`/${department}/${c}`}>
                    {titleCase(c).toUpperCase()}
                  </Link>
                ))}
              </div>
            </div>
            <div className="menu-group sale">
              <span>|03|</span>
              <Link href={`/${department}?sale=true`}>SPECIAL PRICES</Link>
            </div>
            <div className="menu-secondary">
              <Link href="/account">ORDERS</Link>
              <Link href="/favourites">FAVOURITES</Link>
              <Link href="/help/delivery">DELIVERY & RETURNS</Link>
              <Link href="/help/about">ABOUT MYSHOPPE</Link>
            </div>
          </div>
          <Link
            className="menu-preview"
            href={`/collections/${department}-new-in`}
          >
            <img
              src={`/media/campaign-${department}.jpg`}
              alt={`${department} October campaign`}
            />
            <span>
              THE OCTOBER EDIT
              <br />
              2026 / {department.toUpperCase()}
            </span>
          </Link>
        </div>
      </Dialog>
    </>
  );
}
export function Footer() {
  return (
    <footer className="footer">
      <Link className="footer-brand" href="/">
        myshoppe
      </Link>
      <p>CONSIDERED CLOTHING. THOUGHTFUL LIVING.</p>
      <div>
        <Link href="/help/about">ABOUT</Link>
        <Link href="/help/delivery">DELIVERY & RETURNS</Link>
        <Link href="/help/contact">CONTACT</Link>
        <Link href="/help/privacy">PRIVACY</Link>
        <Link href="/help/terms">TERMS</Link>
      </div>
      <div className="footer-bottom">
        <span>INDIA / ENGLISH / INR ₹</span>
        <span>© MYSHOPPE 2026</span>
      </div>
    </footer>
  );
}
