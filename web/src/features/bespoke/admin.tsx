"use client";
import { useEffect, useState } from "react";
import { api, json } from "@/lib/api";
import { ErrorMessage, Loading } from "@/components/ui";
import { useShop } from "@/components/shop-provider";
import { MasterBrief } from "./brief";
import { asset, sameData, statusLabel, type Brief, type Review } from "./data";

export function BespokeAdmin() {
  const shop = useShop();
  const [items, setItems] = useState<Brief[]>([]),
    [selected, setSelected] = useState<Brief | null>(null),
    [review, setReview] = useState<Review>({});
  const [error, setError] = useState<unknown>(null),
    [pending, setPending] = useState(false),
    [loaded, setLoaded] = useState(false),
    [filter, setFilter] = useState("all"),
    [historical, setHistorical] = useState<number | null>(null);
  const permitted = shop.session?.permissions.includes("bespoke.manage");
  const dirty = !!selected && !sameData(review, selected.review);
  async function load() {
    setError(null);
    try {
      setItems(await api<Brief[]>("/admin/bespoke"));
    } catch (e) {
      setError(e);
    } finally {
      setLoaded(true);
    }
  }
  useEffect(() => {
    if (permitted) void load();
  }, [permitted]);
  async function action(action: "review" | "ready") {
    if (!selected || pending) return;
    setPending(true);
    setError(null);
    try {
      const b = await api<Brief>(
        `/admin/bespoke/${selected.id}/actions`,
        json("POST", {
          action,
          expected_version: selected.version,
          instructions: review.instructions || "",
          questions: review.questions || "",
          material_confirmation: review.materials || "",
          measurement_confirmation: review.measurements || "",
        }),
      );
      setSelected(b);
      setReview(b.review);
      setItems((old) => old.map((x) => (x.id === b.id ? b : x)));
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  if (!shop.session) return <Loading />;
  if (!permitted)
    return <p>Owner access is required to review private bespoke briefs.</p>;
  const snapshot =
    historical === null
      ? null
      : selected?.history.find((h) => h.version === historical);
  const display =
    selected && snapshot ? { ...selected, ...snapshot } : selected;
  return (
    <div className="bespoke-admin">
      <div className="admin-title-row">
        <div>
          <p className="studio-kicker">ATELIER / DESIGN REQUESTS</p>
          <h1>Bespoke studio</h1>
        </div>
        <button
          className="button"
          disabled={pending || dirty}
          onClick={() => void load()}
        >
          REFRESH QUEUE
        </button>
      </div>
      <ErrorMessage error={error} />
      {selected ? (
        <>
          <div className="studio-actions">
            <button
              className="button"
              disabled={pending || dirty}
              onClick={() => {
                setSelected(null);
                setHistorical(null);
              }}
            >
              ← ALL DESIGNS
            </button>
            <button
              className="button"
              disabled={dirty}
              onClick={() => window.print()}
            >
              PRINT / SAVE PDF
            </button>
            <button
              className="button"
              disabled={pending}
              onClick={async () => {
                setPending(true);
                try {
                  const b = await api<Brief>(`/admin/bespoke/${selected.id}`);
                  setSelected(b);
                  setReview(b.review);
                  setHistorical(null);
                  setError(null);
                } catch (e) {
                  setError(e);
                } finally {
                  setPending(false);
                }
              }}
            >
              {dirty ? "DISCARD CHANGES & RELOAD" : "RELOAD BRIEF"}
            </button>
          </div>
          {dirty && (
            <p role="status">
              Unsaved review. Save it or discard changes before leaving this
              design. Saving requires renewed customer agreement.
            </p>
          )}
          <div className="studio-review-layout">
            {display && (
              <MasterBrief
                design={display.design}
                brief={display}
                historical={historical !== null}
              />
            )}
            <aside className="brief-aside">
              <p className="studio-kicker">OWNER REVIEW</p>
              <h2>{statusLabel[selected.status]}</h2>
              <p>
                Confirm actual materials and fit. Record the complete
                instructions masterji should follow.
              </p>
              <fieldset disabled={pending || historical !== null}>
                <label className="field">
                  Confirmed materials, quantity & colour
                  <textarea
                    value={review.materials || ""}
                    maxLength={2000}
                    onChange={(e) =>
                      setReview({ ...review, materials: e.target.value })
                    }
                    placeholder="Actual fabric reference, colour, metres, lace quantity…"
                  />
                </label>
                <label className="field">
                  Confirmed measurements / fitting plan
                  <textarea
                    value={review.measurements || ""}
                    maxLength={2000}
                    onChange={(e) =>
                      setReview({ ...review, measurements: e.target.value })
                    }
                    placeholder="Include units and whether measured or awaiting fitting."
                  />
                </label>
                <label className="field">
                  Stitching instructions
                  <textarea
                    rows={7}
                    value={review.instructions || ""}
                    maxLength={6000}
                    onChange={(e) =>
                      setReview({ ...review, instructions: e.target.value })
                    }
                    placeholder="Construction, seam allowance, lining, closures, lace placement and finishing…"
                  />
                </label>
                <label className="field">
                  Open questions
                  <textarea
                    value={review.questions || ""}
                    maxLength={3000}
                    onChange={(e) =>
                      setReview({ ...review, questions: e.target.value })
                    }
                    placeholder="Clear this field when all questions are resolved."
                  />
                </label>
                <button
                  className="button primary"
                  onClick={() => void action("review")}
                >
                  SAVE REVIEW FOR CUSTOMER
                </button>
                {selected.status === "agreed" && (
                  <button
                    className="button primary"
                    disabled={dirty}
                    onClick={() => void action("ready")}
                  >
                    RELEASE TO MASTERJI →
                  </button>
                )}
              </fieldset>
              {selected.status === "ready" && (
                <p role="status">
                  Released. Print this revision for masterji. A changed review
                  requires a new agreement.
                </p>
              )}
              <label className="field">
                View revision
                <select
                  value={historical ?? "latest"}
                  onChange={(e) =>
                    setHistorical(
                      e.target.value === "latest"
                        ? null
                        : Number(e.target.value),
                    )
                  }
                >
                  <option value="latest">Latest · {selected.version}</option>
                  {[...selected.history].reverse().map((h) => (
                    <option key={h.version} value={h.version}>
                      Revision {h.version} · {h.status}
                    </option>
                  ))}
                </select>
              </label>
              {historical !== null && (
                <p>
                  Historical snapshot. Return to the latest revision to review.
                </p>
              )}
            </aside>
          </div>
        </>
      ) : (
        <>
          <label className="field queue-filter">
            Status
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="all">All submitted designs</option>
              {Object.entries(statusLabel)
                .filter(([k]) => k !== "draft")
                .map(([k, v]) => (
                  <option value={k} key={k}>
                    {v}
                  </option>
                ))}
            </select>
          </label>
          {!loaded ? (
            <Loading />
          ) : (
            <div className="bespoke-queue">
              {items
                .filter((b) => filter === "all" || b.status === filter)
                .map((b) => (
                  <button
                    key={b.id}
                    onClick={() => {
                      setSelected(b);
                      setReview(b.review);
                      setHistorical(null);
                    }}
                  >
                    {b.design.fabric && (
                      <img
                        src={asset(b.design.fabric, 360)}
                        alt=""
                        width="100"
                        height="100"
                      />
                    )}
                    <div>
                      <b>{b.design.name || "Untitled design"}</b>
                      <p>
                        {b.design.occasion || "Personal design"} · MS-
                        {b.id.slice(0, 8).toUpperCase()}
                      </p>
                    </div>
                    <span>
                      {statusLabel[b.status]}
                      <small>Revision {b.version}</small>
                    </span>
                    <span>↗</span>
                  </button>
                ))}
              {!items.filter((b) => filter === "all" || b.status === filter)
                .length && <p>No design requests in this view.</p>}
            </div>
          )}
        </>
      )}
    </div>
  );
}
