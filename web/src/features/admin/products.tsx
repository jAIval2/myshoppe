"use client";
import { useShop } from "@/components/shop-provider";
import { ErrorMessage } from "@/components/ui";
import {
  api,
  ApiError,
  json,
  money,
  titleCase,
  type Product,
  type ProductInput,
  type ProductPage,
} from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export function AdminProducts() {
  const [data, setData] = useState<ProductPage | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    const c = new AbortController();
    const t = setTimeout(
      () =>
        api<ProductPage>(`/admin/products?q=${encodeURIComponent(query)}`, {
          signal: c.signal,
        })
          .then(setData)
          .catch((e) => {
            if (e.name !== "AbortError") setError(e);
          }),
      200,
    );
    return () => {
      c.abort();
      clearTimeout(t);
    };
  }, [query]);
  return (
    <>
      <div className="admin-title">
        <div>
          <p className="eyebrow">CATALOGUE</p>
          <h1>Products & inventory</h1>
        </div>
        <Link href="/admin/products/new" className="button primary">
          ADD PRODUCT
        </Link>
      </div>
      <label className="field admin-search">
        Search products
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Name, material or category"
        />
      </label>
      <ErrorMessage error={error} />
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>PRODUCT</th>
              <th>DEPARTMENT</th>
              <th>PRICE</th>
              <th>AVAILABLE</th>
              <th>STATUS</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data?.items.map((p) => (
              <tr key={p.id}>
                <td>
                  <Link
                    className="admin-product-name"
                    href={`/admin/products/${p.id}`}
                  >
                    <img src={p.media[0].src} alt="" />
                    <span>
                      {p.title}
                      <small>{p.variants.length} variants</small>
                    </span>
                  </Link>
                </td>
                <td>{p.department}</td>
                <td>{money(p.price_paise)}</td>
                <td>{p.variants.reduce((n, v) => n + v.available, 0)}</td>
                <td>
                  <span className={`status ${p.status}`}>{p.status}</span>
                </td>
                <td>
                  <Link href={`/admin/products/${p.id}`}>EDIT →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

const blank: ProductInput = {
  title: "",
  slug: "",
  department: "women",
  category: "dresses",
  description: "",
  material: "",
  care: "",
  details: {},
  media: [],
  variants: [
    {
      sku: "",
      colour: "Ecru",
      colour_hex: "#d9d0bd",
      size: "M",
      price_paise: 295000,
    },
  ],
  relations: {},
};
export function ProductEditor({ id }: { id?: string }) {
  const shop = useShop();
  const router = useRouter();
  const [form, setForm] = useState<ProductInput>(blank);
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [delta, setDelta] = useState<Record<string, string>>({});
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const errorSummary = useRef<HTMLDivElement>(null);
  const fieldRefs = useRef<Record<string, HTMLElement | null>>({});

  useEffect(() => {
    if (Object.keys(fieldErrors).length) errorSummary.current?.focus();
  }, [fieldErrors]);

  const fieldId = (path: string) => `product-${path.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  const fieldProps = (path: string) => ({
    id: fieldId(path),
    ref: (element: HTMLElement | null) => {
      fieldRefs.current[path] = element;
    },
    "aria-invalid": fieldErrors[path] ? (true as const) : undefined,
    "aria-describedby": fieldErrors[path] ? `${fieldId(path)}-error` : undefined,
    className: fieldErrors[path] ? "field-invalid" : undefined,
  });
  function updateField(path: string, name: keyof ProductInput, value: unknown) {
    field(name, value);
    setFieldErrors((current) => {
      const next = { ...current };
      delete next[path];
      if (name === "title" && !id) delete next.slug;
      return next;
    });
  }
  function focusField(path: string) {
    const exact = fieldRefs.current[path];
    const row = exact || fieldRefs.current[path.split(".").slice(0, 2).join(".")];
    row?.scrollIntoView({ block: "center", behavior: "smooth" });
    row?.focus({ preventScroll: true });
  }
  function load(p: Product) {
    setProduct(p);
    setForm({
      title: p.title,
      slug: p.slug,
      department: p.department,
      category: p.category,
      description: p.description,
      material: p.material,
      care: p.care,
      details: p.details,
      media: p.media,
      variants: p.variants
        .filter((v) => v.active)
        .map(
          ({
            id,
            sku,
            colour,
            colour_hex,
            size,
            dimensions,
            price_paise,
            compare_at_paise,
          }) => ({
            id,
            sku,
            colour,
            colour_hex,
            size,
            dimensions,
            price_paise,
            compare_at_paise,
          }),
        ),
      expected_version: p.version,
      relations: p.relations,
    });
  }
  useEffect(() => {
    if (id) api<Product>(`/admin/products/${id}`).then(load).catch(setError);
  }, [id]);
  const field = (name: keyof ProductInput, value: unknown) =>
    setForm((f) => ({ ...f, [name]: value }));
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setFieldErrors({});
    try {
      const result = await api<Product>(
        id ? `/admin/products/${id}` : "/admin/products",
        json(id ? "PATCH" : "POST", form),
      );
      load(result);
      shop.notify("Product saved");
      if (!id) router.replace(`/admin/products/${result.id}`);
    } catch (e) {
      if (e instanceof ApiError && e.fields && Object.keys(e.fields).length) {
        setFieldErrors(e.fields);
      } else {
        setError(e);
      }
    } finally {
      setBusy(false);
    }
  }
  async function upload(file: File) {
    setBusy(true);
    setError(null);
    try {
      const body = new FormData();
      body.set("file", file);
      const media = await api<{ src: string }>("/admin/media", {
        method: "POST",
        body,
      });
      field("media", [
        ...form.media,
        {
          src: media.src,
          alt: form.title || "Product photograph",
          role: form.media.length ? "continuation" : "lead",
        },
      ]);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  async function status(action: string) {
    if (!product) return;
    if (
      action === "archive" &&
      !confirm(
        "Archive this product? It will be removed from the storefront. Existing order records stay intact.",
      )
    )
      return;
    setBusy(true);
    setError(null);
    try {
      load(
        await api<Product>(
          `/admin/products/${product.id}/${action}`,
          json("POST", { expected_version: product.version }),
        ),
      );
      shop.notify(
        action === "archive" ? "Product archived" : "Product published",
      );
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Link href="/admin/products" className="text-link">
        ← PRODUCTS
      </Link>
      <div className="admin-title">
        <h1>{id ? "Edit product" : "New product"}</h1>
        {product && (
          <span className="status" title="Revision number used to prevent stale edits from overwriting newer changes.">
            {product.status} / Revision {product.version}
          </span>
        )}
      </div>
      <ErrorMessage error={error} />
      {Object.keys(fieldErrors).length > 0 && (
        <div className="field-error-summary" role="alert" aria-labelledby="product-error-title" ref={errorSummary} tabIndex={-1}>
          <h2 id="product-error-title">This product needs a few corrections</h2>
          <p>Review the fields below, then save again. Your other changes are still here.</p>
          <ul>
            {Object.entries(fieldErrors).map(([path, message]) => (
              <li key={path}>
                <button type="button" onClick={() => focusField(path)}>
                  {path.split(".").map((part) => /^\d+$/.test(part) ? `variant ${Number(part) + 1}` : titleCase(part)).join(" / ")}: {message}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <form onSubmit={save}>
        <fieldset className="product-editor-fields" disabled={busy}>
        <div className="editor-grid">
          <section className="admin-panel">
            <h2>Product details</h2>
            {(["title", "slug", "category", "material"] as const).map(
              (name) => (
                <label className="field" key={name}>
                  {titleCase(name)}
                  <input
                    {...fieldProps(name)}
                    required
                    value={form[name]}
                    onChange={(e) => {
                      updateField(name, name, e.target.value);
                      if (name === "title" && !id)
                        field(
                          "slug",
                          e.target.value
                            .toLowerCase()
                            .replace(/[^a-z0-9]+/g, "-")
                            .replace(/-$/, ""),
                        );
                    }}
                  />
                  {fieldErrors[name] && <small className="field-error" id={`${fieldId(name)}-error`}>{fieldErrors[name]}</small>}
                </label>
              ),
            )}
            <label className="field">
              Department
              <select
                {...fieldProps("department")}
                value={form.department}
                onChange={(e) => updateField("department", "department", e.target.value)}
              >
                <option value="women">Women</option>
                <option value="home">Home</option>
              </select>
              {fieldErrors.department && <small className="field-error" id={`${fieldId("department")}-error`}>{fieldErrors.department}</small>}
            </label>
            {(["description", "care"] as const).map((name) => (
              <label className="field" key={name}>
                {titleCase(name)}
                <textarea
                  {...fieldProps(name)}
                  required
                  value={form[name]}
                  onChange={(e) => updateField(name, name, e.target.value)}
                />
                {fieldErrors[name] && <small className="field-error" id={`${fieldId(name)}-error`}>{fieldErrors[name]}</small>}
              </label>
            ))}
            {(form.department === "home"
              ? ["dimensions", "contents", "type"]
              : ["fit", "measurements"]
            ).map((name) => (
              <label className="field" key={name}>
                {titleCase(name)}
                <input
                  {...fieldProps(`details.${name}`)}
                  required
                  value={form.details?.[name] || ""}
                  onChange={(e) =>
                    updateField(`details.${name}`, "details", {
                      ...form.details,
                      [name]: e.target.value,
                    })
                  }
                />
                {fieldErrors[`details.${name}`] && <small className="field-error" id={`${fieldId(`details.${name}`)}-error`}>{fieldErrors[`details.${name}`]}</small>}
              </label>
            ))}
          </section>
          <section className="admin-panel">
            <h2>Photography</h2>
            <p className="muted">
              Lead + 4 continuation images + cutout required to publish. Use
              verified photographs of this product.
            </p>
            <label className="upload-area">
              ADD PHOTOGRAPH
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                disabled={busy}
                onChange={(e) => {
                  if (e.target.files?.[0]) upload(e.target.files[0]);
                }}
              />
            </label>
            <div className="media-editor">
              {form.media.map((m, i) => (
                <div key={`${m.src}-${i}`} tabIndex={-1} ref={(element) => { fieldRefs.current[`media.${i}`] = element; }}>
                  <img src={m.src} alt={m.alt} />
                  <label>
                    Image role
                    <select
                      {...fieldProps(`media.${i}.role`)}
                      value={m.role}
                      onChange={(e) =>
                        updateField(
                          `media.${i}.role`,
                          "media",
                          form.media.map((a, n) =>
                            n === i ? { ...a, role: e.target.value } : a,
                          ),
                        )
                      }
                    >
                      {["lead", "continuation", "cutout", "editorial"].map(
                        (r) => (
                          <option key={r}>{r}</option>
                        ),
                      )}
                    </select>
                    {fieldErrors[`media.${i}.role`] && <small className="field-error" id={`${fieldId(`media.${i}.role`)}-error`}>{fieldErrors[`media.${i}.role`]}</small>}
                  </label>
                  <label>
                    Alternative text
                    <input
                      {...fieldProps(`media.${i}.alt`)}
                      value={m.alt}
                      onChange={(e) =>
                        updateField(
                          `media.${i}.alt`,
                          "media",
                          form.media.map((a, n) =>
                            n === i ? { ...a, alt: e.target.value } : a,
                          ),
                        )
                      }
                      />
                    {fieldErrors[`media.${i}.alt`] && <small className="field-error" id={`${fieldId(`media.${i}.alt`)}-error`}>{fieldErrors[`media.${i}.alt`]}</small>}
                  </label>
                  <div>
                    <button
                      type="button"
                      disabled={i === 0}
                      onClick={() => {
                        const next = [...form.media];
                        [next[i - 1], next[i]] = [next[i], next[i - 1]];
                        field("media", next);
                      }}
                    >
                      MOVE UP
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        field(
                          "media",
                          form.media.filter((_, n) => n !== i),
                        )
                      }
                    >
                      REMOVE
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
        <section className="admin-panel">
          <h2>Variants & prices</h2>
          <details className="relation-editor">
            <summary>CURATED PRODUCT LINKS</summary>
            <p>
              Enter published product IDs or slugs separated by commas. Only
              products in the same department will appear.
            </p>
            {["complements", "suggestions"].map((key) => (
              <label className="field" key={key}>
                {titleCase(key)}
                <input
                  value={(form.relations?.[key] || []).join(", ")}
                  onChange={(e) =>
                    field("relations", {
                      ...form.relations,
                      [key]: e.target.value
                        .split(",")
                        .map((v) => v.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </label>
            ))}
          </details>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>COLOUR</th>
                  <th>SWATCH</th>
                  <th>SIZE</th>
                  <th>DIMENSIONS</th>
                  <th>PRICE ₹</th>
                  <th>COMPARE ₹</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {form.variants.map((v, i) => (
                  <tr key={v.id || v.sku} tabIndex={-1} ref={(element) => { fieldRefs.current[`variants.${i}`] = element; }}>
                    {(
                      [
                        "sku",
                        "colour",
                        "colour_hex",
                        "size",
                        "dimensions",
                        "price_paise",
                        "compare_at_paise",
                      ] as const
                    ).map((k) => (
                      <td key={k}>
                        <input
                          {...fieldProps(`variants.${i}.${k}`)}
                          aria-label={`${k} variant ${i + 1}`}
                          required={
                            k !== "dimensions" && k !== "compare_at_paise"
                          }
                          type={
                            k.includes("paise")
                              ? "number"
                              : k === "colour_hex"
                                ? "color"
                                : "text"
                          }
                          min={k.includes("paise") ? "1" : undefined}
                          value={
                            k.includes("paise")
                              ? v[k]
                                ? Number(v[k]) / 100
                                : ""
                              : v[k] || ""
                          }
                          onChange={(e) =>
                            updateField(
                              `variants.${i}.${k}`,
                              "variants",
                              form.variants.map((a, n) =>
                                n === i
                                  ? {
                                      ...a,
                                      [k]: k.includes("paise")
                                        ? e.target.value
                                          ? Math.round(
                                              Number(e.target.value) * 100,
                                            )
                                          : null
                                        : e.target.value,
                                    }
                                  : a,
                              ),
                            )
                          }
                        />
                        {fieldErrors[`variants.${i}.${k}`] && <small className="field-error" id={`${fieldId(`variants.${i}.${k}`)}-error`}>{fieldErrors[`variants.${i}.${k}`]}</small>}
                      </td>
                    ))}
                    <td>
                      <button
                        type="button"
                        disabled={form.variants.length === 1}
                        onClick={() =>
                          field(
                            "variants",
                            form.variants.filter((_, n) => n !== i),
                          )
                        }
                      >
                        REMOVE
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            className="text-link"
            type="button"
            onClick={() =>
              field("variants", [
                ...form.variants,
                { ...blank.variants[0], sku: `NEW-${Date.now()}` },
              ])
            }
          >
            + ADD VARIANT
          </button>
        </section>
        </fieldset>
        <div className="editor-actions">
          <button className="button primary" disabled={busy}>
            SAVE PRODUCT
          </button>
          {product && (
            <>
              <button
                className="button"
                type="button"
                disabled={busy}
                onClick={() => status("publish")}
              >
                PUBLISH
              </button>
              <button
                className="button"
                type="button"
                disabled={busy}
                onClick={() => status("archive")}
              >
                ARCHIVE
              </button>
              <Link href={`/products/${product.slug}`} className="text-link">
                VIEW IN STORE ↗
              </Link>
            </>
          )}
        </div>
      </form>
      {product && (
        <section className="admin-panel">
          <h2>Inventory adjustments</h2>
          <p className="muted">
            Adjustments preserve active checkout reservations and create an
            audit record.
          </p>
          {product.variants.map((v) => (
            <div className="stock-row" key={v.id}>
              <span>
                {v.sku} / {v.size} / {v.colour}
              </span>
              <span>
                {v.on_hand} ON HAND · {v.reserved} RESERVED
              </span>
              <input
                type="number"
                aria-label={`Adjustment ${v.sku}`}
                placeholder="+ / −"
                value={delta[v.id] || ""}
                onChange={(e) => setDelta({ ...delta, [v.id]: e.target.value })}
              />
              <button
                className="button"
                onClick={async () => {
                  const reason = prompt("Reason for this stock adjustment");
                  if (!reason) return;
                  try {
                    await api(
                      "/admin/inventory/adjustments",
                      json("POST", {
                        variant_id: v.id,
                        delta: Number(delta[v.id]),
                        reason,
                        request_key: crypto.randomUUID(),
                      }),
                    );
                    load(await api<Product>(`/admin/products/${id}`));
                    setDelta({ ...delta, [v.id]: "" });
                  } catch (e) {
                    setError(e);
                  }
                }}
              >
                ADJUST
              </button>
            </div>
          ))}
        </section>
      )}
    </>
  );
}
