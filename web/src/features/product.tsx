"use client";
import { useState } from "react";
import Link from "next/link";
import { money, type Product } from "@/lib/api";
import { useShop } from "@/components/shop-provider";
import { Dialog, Icon, ErrorMessage } from "@/components/ui";
import { ProductCard } from "@/components/product-card";
import { Footer } from "@/components/shell";

export function ProductDetail({
  product,
  related,
}: {
  product: Product;
  related: Product[];
}) {
  const shop = useShop();
  const [zoom, setZoom] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const colours = [
    ...new Map(product.variants.map((v) => [v.colour, v])).values(),
  ];
  const [colour, setColour] = useState(colours[0]?.colour || "");
  const selected = product.variants.filter((v) => v.colour === colour);
  const price = Math.min(...selected.map((v) => v.price_paise));
  const curated = (key: string) =>
    (product.relations?.[key] || []).flatMap((id) =>
      related.filter((p) => p.id === id || p.slug === id),
    );
  const complement = curated("complements").length
    ? curated("complements").slice(0, 4)
    : related.slice(0, 2);
  const suggestions = (
    curated("suggestions").length ? curated("suggestions") : related
  )
    .filter((p) => !complement.some((c) => c.id === p.id))
    .slice(0, 12);
  return (
    <main id="main" className="product-page">
      <div className="product-opening">
        <button
          className="lead-image"
          onClick={() => setZoom(product.media[0].src)}
          aria-label="Zoom product image"
        >
          <img
            src={product.media[0].src}
            alt={product.media[0].alt}
            fetchPriority="high"
          />
        </button>
        <div className="purchase-panel">
          <div className="product-title-row">
            <h1>{product.title}</h1>
            <button
              className="icon-button"
              aria-label={
                shop.saved.has(product.id)
                  ? "Remove from favourites"
                  : "Save to favourites"
              }
              aria-pressed={shop.saved.has(product.id)}
              onClick={() => shop.save(product.id).catch(setError)}
            >
              <Icon name="bookmark" />
            </button>
          </div>
          <p className="pdp-price">{money(price)}</p>
          <p className="micro muted">MRP INCL. OF ALL TAXES</p>
          <hr />
          <p className="micro">
            {colour.toUpperCase()} / {selected[0]?.sku}
          </p>
          <div className="swatches">
            {colours.map((v) => (
              <button
                className={colour === v.colour ? "selected" : ""}
                key={v.colour}
                aria-label={v.colour}
                aria-pressed={colour === v.colour}
                onClick={() => setColour(v.colour)}
              >
                <span style={{ background: v.colour_hex }} />
              </button>
            ))}
          </div>
          <button
            className="button pdp-add"
            onClick={() =>
              shop.quickAdd({
                ...product,
                variants: [
                  ...selected,
                  ...product.variants.filter((v) => v.colour !== colour),
                ],
              })
            }
          >
            ADD
          </button>
          <ErrorMessage error={error} />
          <p className="product-description">{product.description}</p>
          {product.department === "home" && (
            <div className="textile-facts">
              <p>{product.details?.dimensions}</p>
              <p>{product.details?.contents}</p>
              <p>{product.details?.type}</p>
            </div>
          )}
          <section className="complements">
            <h2>
              {product.department === "home"
                ? "COMPLETE YOUR SPACE"
                : "COMPLETE YOUR LOOK"}
            </h2>
            <div>
              {complement.map((p) => (
                <Link href={`/products/${p.slug}`} key={p.id}>
                  <img
                    src={
                      p.media.find((m) => m.role === "cutout")?.src ||
                      p.media[0].src
                    }
                    alt={p.title}
                  />
                  <span>{p.title}</span>
                </Link>
              ))}
            </div>
          </section>
          <div className="product-details">
            {[
              [
                product.department === "home"
                  ? "DIMENSIONS & CONTENTS"
                  : "PRODUCT MEASUREMENTS",
                Object.entries(product.details || {})
                  .map(([key, value]) => `${key}: ${value}`)
                  .join("\n"),
              ],
              [
                "COMPOSITION, CARE & ORIGIN",
                `${product.material}\n${product.care}`,
              ],
              [
                "SHIPPING, EXCHANGES AND RETURNS",
                "Review delivery and return details before placing your order.",
              ],
            ].map(([title, text]) => (
              <details key={title}>
                <summary>
                  {title}
                  <Icon name="plus" size={16} />
                </summary>
                <p>{text}</p>
                {title.startsWith("SHIPPING") && (
                  <Link href="/help/delivery">DELIVERY & RETURNS</Link>
                )}
              </details>
            ))}
          </div>
        </div>
      </div>
      <nav className="collection-strip" aria-label="Explore this collection">
        {[product, ...related].slice(0, 16).map((p) => (
          <Link
            href={`/products/${p.slug}`}
            key={p.id}
            aria-current={product.id === p.id ? "page" : undefined}
          >
            <img
              src={
                p.media.find((m) => m.role === "cutout")?.src || p.media[0].src
              }
              alt={p.title}
            />
            <span>{product.id === p.id ? "•" : ""}</span>
          </Link>
        ))}
      </nav>
      <section className="continuation-gallery" aria-label="Product gallery">
        {product.media
          .filter((m) => m.role === "continuation")
          .map((m, i) => (
            <button
              key={i}
              onClick={() => setZoom(m.src)}
              aria-label={`Zoom image ${i + 2}`}
            >
              <img src={m.src} alt={m.alt} loading="lazy" />
            </button>
          ))}
      </section>
      <section className="suggestions">
        <h2>YOU MAY BE INTERESTED IN</h2>
        <div className="product-grid view-3">
          {suggestions.map((p) => (
            <ProductCard key={p.id} product={p} compact />
          ))}
        </div>
      </section>
      <div className="mobile-purchase">
        <span>{money(price)}</span>
        <button className="button" onClick={() => shop.quickAdd(product)}>
          ADD
        </button>
      </div>
      <Dialog
        open={!!zoom}
        onClose={() => setZoom(null)}
        title="Product image"
        className="zoom-dialog"
      >
        {zoom && <img src={zoom} alt={product.title} />}
      </Dialog>
      <Footer />
    </main>
  );
}
