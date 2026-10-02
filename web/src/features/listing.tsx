"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  api,
  categories,
  titleCase,
  type ProductPage,
  type Department,
} from "@/lib/api";
import { Dialog, ErrorMessage, Loading } from "@/components/ui";
import { ProductCard } from "@/components/product-card";

export function Listing({
  initial,
  department,
  category,
  embedded = false,
  search = false,
}: {
  initial: ProductPage;
  department?: Department;
  category?: string;
  embedded?: boolean;
  search?: boolean;
}) {
  const [data, setData] = useState(initial);
  const [view, setView] = useState(1);
  const [filterOpen, setFilterOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("new");
  const [colour, setColour] = useState("");
  const [size, setSize] = useState("");
  const [available, setAvailable] = useState(false);
  const [sale, setSale] = useState(false);
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const stage = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const read = () => {
      const p = new URLSearchParams(location.search);
      setView(
        [1, 2, 3].includes(Number(p.get("view"))) ? Number(p.get("view")) : 1,
      );
      setQuery(p.get("q") || "");
      setSort(p.get("sort") || "new");
      setColour(p.get("colour") || "");
      setSize(p.get("size") || "");
      setAvailable(p.get("available") === "true");
      setSale(p.get("sale") === "true");
      setPage(Math.max(1, Number(p.get("page")) || 1));
      setReady(true);
    };
    read();
    addEventListener("popstate", read);
    return () => removeEventListener("popstate", read);
  }, []);
  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    const timer = setTimeout(
      () => {
        const params = new URLSearchParams();
        if (department) params.set("department", department);
        if (category) params.set("category", category);
        if (query) params.set("q", query);
        if (colour) params.set("colour", colour);
        if (size) params.set("size", size);
        if (available) params.set("available", "true");
        if (sale) params.set("sale", "true");
        params.set("sort", sort);
        params.set("page", String(page));
        setBusy(true);
        setError(null);
        api<ProductPage>(`/products?${params}`, { signal: controller.signal })
          .then(setData)
          .catch((e) => {
            if (e.name !== "AbortError") setError(e);
          })
          .finally(() => {
            if (!controller.signal.aborted) setBusy(false);
          });
        if (!embedded) {
          params.set("view", String(view));
          history.replaceState(
            history.state,
            "",
            `${location.pathname}?${params}`,
          );
        }
      },
      search ? 250 : 0,
    );
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [
    department,
    category,
    query,
    sort,
    colour,
    size,
    available,
    sale,
    page,
    ready,
    search,
    embedded,
  ]);
  function changeView(next: number) {
    const cards = Array.from(
      stage.current?.querySelectorAll<HTMLElement>("[data-product-id]") || [],
    );
    const anchor = cards.find((el) => el.getBoundingClientRect().bottom > 100);
    const id = anchor?.dataset.productId;
    const top = anchor?.getBoundingClientRect().top || 0;
    setView(next);
    const params = new URLSearchParams(location.search);
    params.set("view", String(next));
    history.replaceState(history.state, "", `${location.pathname}?${params}`);
    requestAnimationFrame(() => {
      if (!id) return;
      const el = stage.current?.querySelector<HTMLElement>(
        `[data-product-id="${id}"]`,
      );
      if (el)
        scrollBy({
          top: el.getBoundingClientRect().top - top,
          behavior: "instant",
        });
    });
  }
  const label = search
    ? "SEARCH"
    : category
      ? titleCase(category)
      : sale
        ? "SPECIAL PRICES"
        : "THE NEW";
  return (
    <div className={`listing ${embedded ? "embedded-listing" : ""}`}>
      <aside className="category-rail" aria-label="Collection categories">
        <Link
          className={!category ? "active" : ""}
          href={`/${department || "women"}`}
        >
          |01| VIEW ALL
        </Link>
        {department &&
          categories[department].map((cat, i) => (
            <Link
              key={cat}
              className={category === cat ? "active" : ""}
              href={`/${department}/${cat}`}
            >
              |{String(i + 2).padStart(2, "0")}| {titleCase(cat).toUpperCase()}
            </Link>
          ))}
        <button className="filter-trigger" onClick={() => setFilterOpen(true)}>
          FILTERS {(colour || size || available || sale) && "•"}
        </button>
      </aside>
      <div className="view-control">
        <span>VIEW</span>
        <div role="group" aria-label="Product view">
          {[1, 2, 3].map((n) => (
            <button
              key={n}
              onClick={() => changeView(n)}
              aria-label={`View ${n}: ${["Editorial", "Gallery", "Compact"][n - 1]}`}
              aria-pressed={view === n}
            >
              {n}
            </button>
          ))}
        </div>
      </div>
      <div className="catalogue-stage" ref={stage}>
        <div className="listing-heading">
          <h1>{label}</h1>
          <span>{data.total} ITEMS</span>
          <button className="mobile-filter" onClick={() => setFilterOpen(true)}>
            FILTERS
          </button>
        </div>
        {search && (
          <form className="search-form" onSubmit={(e) => e.preventDefault()}>
            <label htmlFor="search">WHAT ARE YOU LOOKING FOR?</label>
            <input
              id="search"
              autoFocus
              placeholder="Linen, a dress, a quieter home…"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
            />
            <div>
              {["linen", "dress", "duvet cover"].map((term) => (
                <button key={term} onClick={() => setQuery(term)} type="button">
                  {term.toUpperCase()}
                </button>
              ))}
            </div>
          </form>
        )}
        <ErrorMessage error={error} />
        {busy && (
          <span className="results-loading" role="status">
            UPDATING…
          </span>
        )}
        {!data.items.length && !busy ? (
          <div className="empty-state">
            <h2>Nothing here, just yet.</h2>
            <p>Try a different search or clear your filters.</p>
            <button
              className="text-link"
              onClick={() => {
                setColour("");
                setSize("");
                setAvailable(false);
                setSale(false);
                setQuery("");
              }}
            >
              CLEAR FILTERS
            </button>
          </div>
        ) : (
          <>
            {view === 1 &&
              department &&
              !category &&
              !search &&
              !query &&
              !colour &&
              !size &&
              !sale &&
              page === 1 && (
                <section
                  className="collection-panels"
                  aria-label="Explore the collection"
                >
                  {categories[department].slice(0, 4).map((cat, index) => (
                    <Link key={cat} href={`/${department}/${cat}`}>
                      <img
                        src={
                          data.items[(index * 5) % data.items.length].media[0]
                            .src
                        }
                        alt=""
                        loading="lazy"
                      />
                      <span>{titleCase(cat).toUpperCase()}</span>
                    </Link>
                  ))}
                </section>
              )}
            <div className={`product-grid view-${view}`} aria-busy={busy}>
              {data.items.map((p, i) => (
                <ProductCard
                  key={p.id}
                  product={p}
                  compact={view === 3}
                  priority={i < 4}
                />
              ))}
            </div>
          </>
        )}
        <nav className="pagination" aria-label="Results pages">
          <button
            disabled={page <= 1 || busy}
            onClick={() => {
              setPage((p) => p - 1);
              stage.current?.scrollIntoView();
            }}
          >
            PREVIOUS
          </button>
          <span>
            {page} / {data.pages}
          </span>
          <button
            disabled={page >= data.pages || busy}
            onClick={() => {
              setPage((p) => p + 1);
              stage.current?.scrollIntoView();
            }}
          >
            NEXT
          </button>
        </nav>
      </div>
      <Dialog
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        title="Filters"
        className="filter-dialog"
      >
        <h2>FILTERS & SORT</h2>
        <label className="field">
          Sort
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="new">New in</option>
            <option value="price-asc">Price, low to high</option>
            <option value="price-desc">Price, high to low</option>
            <option value="name">Name</option>
          </select>
        </label>
        <label className="field">
          Colour
          <select
            value={colour}
            onChange={(e) => {
              setColour(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All colours</option>
            <option>Ecru</option>
            <option>Black</option>
          </select>
        </label>
        <label className="field">
          Size
          <select
            value={size}
            onChange={(e) => {
              setSize(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All sizes</option>
            {(department === "home"
              ? ["Queen", "King"]
              : ["XS", "S", "M", "L"]
            ).map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label className="check-field">
          <input
            type="checkbox"
            checked={available}
            onChange={(e) => setAvailable(e.target.checked)}
          />{" "}
          In stock only
        </label>
        <label className="check-field">
          <input
            type="checkbox"
            checked={sale}
            onChange={(e) => setSale(e.target.checked)}
          />{" "}
          Special prices
        </label>
        <button className="button primary" onClick={() => setFilterOpen(false)}>
          VIEW {data.total} ITEMS
        </button>
        <button
          className="button borderless"
          onClick={() => {
            setColour("");
            setSize("");
            setAvailable(false);
            setSale(false);
            setSort("new");
          }}
        >
          CLEAR
        </button>
      </Dialog>
    </div>
  );
}
