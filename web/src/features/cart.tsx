"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, money, type Product, type ProductPage } from "@/lib/api";
import { useShop } from "@/components/shop-provider";
import { Icon, ErrorMessage, Empty } from "@/components/ui";
import { ProductCard } from "@/components/product-card";

export function Bag() {
  const shop = useShop();
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState("");
  const [suggestions, setSuggestions] = useState<Product[]>([]);
  useEffect(() => {
    api<ProductPage>("/products?limit=6")
      .then((d) => setSuggestions(d.items))
      .catch(setError);
  }, []);
  async function change(id: string, quantity: number) {
    setBusy(id);
    setError(null);
    try {
      await shop.changeQuantity(id, quantity);
    } catch (e) {
      setError(e);
    } finally {
      setBusy("");
    }
  }
  return (
    <main id="main" className="bag-page">
      <h1 className="sr-only">Your shopping bag</h1>
      <ErrorMessage error={error} />
      {!shop.cart.items.length ? (
        <Empty title="Your bag is waiting.">
          <p>A few considered pieces. Something that feels like you.</p>
          <Link className="button" href="/women">
            EXPLORE THE COLLECTION
          </Link>
        </Empty>
      ) : (
        <>
          <div className="bag-items">
            {shop.cart.items.map((item) => (
              <article key={item.variant_id} className="bag-item">
                <Link href={`/products/${item.slug}`}>
                  <img src={item.image} alt={item.title} />
                </Link>
                <div className="bag-item-details">
                  <div className="bag-title">
                    <Link href={`/products/${item.slug}`}>{item.title}</Link>
                    <button
                      className="icon-button"
                      aria-label={`Save ${item.title}`}
                      aria-pressed={shop.saved.has(item.product_id)}
                      onClick={() => shop.save(item.product_id).catch(setError)}
                    >
                      <Icon name="bookmark" size={17} />
                    </button>
                  </div>
                  <p>
                    {item.size} | {item.colour.toUpperCase()}
                  </p>
                  <p>{money(item.price_paise)}</p>
                  {item.available <= 2 && (
                    <p className="micro">FEW ITEMS LEFT</p>
                  )}
                  {item.status !== "published" && (
                    <p className="error">NO LONGER AVAILABLE</p>
                  )}
                  <div className="quantity">
                    <button
                      aria-label={`Decrease ${item.title}`}
                      disabled={!!busy || item.quantity <= 1}
                      onClick={() => change(item.variant_id, item.quantity - 1)}
                    >
                      −
                    </button>
                    <span aria-live="polite">{item.quantity}</span>
                    <button
                      aria-label={`Increase ${item.title}`}
                      disabled={
                        !!busy || item.quantity >= Math.min(10, item.available)
                      }
                      onClick={() => change(item.variant_id, item.quantity + 1)}
                    >
                      +
                    </button>
                  </div>
                  <button
                    className="text-link delete"
                    disabled={!!busy}
                    onClick={() => change(item.variant_id, 0)}
                  >
                    DELETE
                  </button>
                </div>
              </article>
            ))}
          </div>
          <div className="checkout-bar">
            <Link href="/favourites">YOUR FAVOURITES</Link>
            <div>
              <div className="bag-total">
                <span>{money(shop.cart.subtotal)}</span>
                <small>
                  Including GST
                  <br />
                  Shipping calculated at checkout
                </small>
              </div>
              <Link className="button primary" href="/checkout">
                CONTINUE ({shop.cart.count})
              </Link>
            </div>
          </div>
        </>
      )}
      <section className="bag-suggestions">
        <h2>YOU MAY ALSO LIKE</h2>
        <div className="product-grid view-3">
          {suggestions.map((p) => (
            <ProductCard key={p.id} product={p} compact />
          ))}
        </div>
      </section>
    </main>
  );
}
export function Favourites() {
  const shop = useShop();
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    if (shop.session)
      api<Product[]>("/favourites").then(setProducts).catch(setError);
  }, [shop.saved, shop.session]);
  return (
    <main id="main" className="saved-page">
      <h1>FAVOURITES</h1>
      <ErrorMessage error={error} />
      {products.length ? (
        <div className="product-grid view-2">
          {products.map((p) => (
            <div key={p.id}>
              <ProductCard product={p} />
              <button
                className="text-link"
                onClick={() => shop.save(p.id).catch(setError)}
              >
                REMOVE
              </button>
            </div>
          ))}
        </div>
      ) : (
        <Empty title="A collection of your own.">
          <p>Save the pieces you want to come back to.</p>
          <Link className="button" href="/women">
            EXPLORE
          </Link>
        </Empty>
      )}
    </main>
  );
}
