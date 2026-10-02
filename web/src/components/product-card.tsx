"use client";
import Link from "next/link";
import { money, type Product } from "@/lib/api";
import { useShop } from "./shop-provider";
import { Icon } from "./ui";

export function ProductCard({
  product,
  compact = false,
  priority = false,
}: {
  product: Product;
  compact?: boolean;
  priority?: boolean;
}) {
  const shop = useShop();
  const media = compact
    ? product.media.find((m) => m.role === "cutout") || product.media[0]
    : product.media[0];
  return (
    <article
      className={`product-card ${compact ? "compact-card" : ""}`}
      data-product-id={product.id}
    >
      <Link href={`/products/${product.slug}`} className="product-image">
        <img
          src={media?.src}
          alt={media?.alt || product.title}
          loading={priority ? "eager" : "lazy"}
        />
        <span className="image-caption">{product.title}</span>
      </Link>
      <div className="product-caption">
        <Link href={`/products/${product.slug}`} className="product-name">
          {product.title}
        </Link>
        <span className="price">{money(product.price_paise)}</span>
        <button
          className="card-add icon-button"
          aria-label={`Add ${product.title}`}
          onClick={() => shop.quickAdd(product)}
        >
          <Icon name="plus" size={18} />
        </button>
      </div>
      {!compact && (
        <div className="card-colours" aria-label="Available colours">
          {[
            ...new Map(product.variants.map((v) => [v.colour, v])).values(),
          ].map((v) => (
            <span
              key={v.colour}
              title={v.colour}
              style={{ background: v.colour_hex }}
            />
          ))}
        </div>
      )}
    </article>
  );
}
