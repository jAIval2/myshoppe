"use client";
import { useState } from "react";
import { money, type Product, type Variant } from "@/lib/api";
import { ErrorMessage } from "./ui";

export function VariantPicker({
  product,
  onAdd,
}: {
  product: Product;
  onAdd: (variant: Variant) => Promise<void>;
}) {
  const [colour, setColour] = useState(product.variants[0]?.colour || "");
  const [selected, setSelected] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const colours = [
    ...new Map(product.variants.map((v) => [v.colour, v])).values(),
  ];
  const variants = product.variants.filter(
    (v) => v.colour === colour && v.active,
  );
  const chosen = variants.find((v) => v.id === selected);
  async function add() {
    if (!chosen) {
      setError(new Error("Choose a size to continue."));
      return;
    }
    setPending(true);
    setError(null);
    try {
      await onAdd(chosen);
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  return (
    <div className="variant-picker">
      <div className="variant-price">
        {money(
          chosen?.price_paise ??
            Math.min(...variants.map((v) => v.price_paise)),
        )}
      </div>
      <p className="micro">
        {colour.toUpperCase()} {chosen ? ` / ${chosen.sku}` : ""}
      </p>
      <div className="swatches" aria-label="Colour">
        {colours.map((v) => (
          <button
            key={v.colour}
            className={colour === v.colour ? "selected" : ""}
            aria-label={v.colour}
            aria-pressed={colour === v.colour}
            onClick={() => {
              setColour(v.colour);
              setSelected("");
              setError(null);
            }}
          >
            <span style={{ background: v.colour_hex }} />
          </button>
        ))}
      </div>
      <fieldset className="sizes">
        <legend>
          {product.department === "home" ? "SIZE / DIMENSIONS" : "SELECT SIZE"}
        </legend>
        {variants.map((v) => (
          <button
            type="button"
            key={v.id}
            disabled={v.available < 1}
            aria-pressed={selected === v.id}
            className={selected === v.id ? "selected" : ""}
            onClick={() => {
              setSelected(v.id);
              setError(null);
            }}
          >
            {v.size}
            {v.dimensions && <span>{v.dimensions}</span>}
            {v.available < 1 && <small>Out of stock</small>}
          </button>
        ))}
      </fieldset>
      <ErrorMessage error={error} />
      <button className="button" onClick={add} disabled={pending}>
        {pending ? "ADDING…" : "ADD TO BAG"}
      </button>
      <p className="micro muted">
        {chosen && chosen.available <= 2
          ? "FEW ITEMS LEFT"
          : "Choose your size. Find your fit."}
      </p>
    </div>
  );
}
