"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, json } from "@/lib/api";
import { Dialog, ErrorMessage } from "@/components/ui";
import { useShop } from "@/components/shop-provider";
import {
  asset,
  fabrics,
  laces,
  material,
  fresh,
  sameData,
  designFields,
  statusLabel,
  type Material,
  type Design,
  type Brief,
} from "./data";
import { DesignBoard } from "./board";
import { MasterBrief } from "./brief";

export function BespokeStudio() {
  const shop = useShop();
  const [d, setD] = useState<Design>(fresh),
    [brief, setBrief] = useState<Brief | null>(null),
    [step, setStep] = useState(0);
  const [filter, setFilter] = useState("All"),
    [query, setQuery] = useState("");
  const [zoom, setZoom] = useState<Material | null>(null),
    [saved, setSaved] = useState<Brief[]>([]),
    [library, setLibrary] = useState(false);
  const [pending, setPending] = useState(false),
    [mediaBusy, setMediaBusy] = useState(false),
    [error, setError] = useState<unknown>(null),
    [notice, setNotice] = useState("");
  const [recovery, setRecovery] = useState<{
      design: Design;
      baseVersion: number;
      id: string | null;
    } | null>(null),
    [initialized, setInitialized] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [reloadConfirm, setReloadConfirm] = useState(false);
  const title = useRef<HTMLHeadingElement>(null),
    current = useRef(d),
    record = useRef(brief),
    locked = useRef(false);
  current.current = d;
  record.current = brief;
  const dirty = !sameData(d, brief?.design || fresh());
  const selected = material(d.fabric);
  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("design");
    let alive = true;
    (async () => {
      try {
        let server: Brief | null = null;
        if (id) {
          server = await api<Brief>(`/bespoke/${id}`);
          if (!alive) return;
          setBrief(server);
          setD(server.design);
          setStep(3);
        }
        const raw = sessionStorage.getItem(`bespoke-recovery:${id || "new"}`);
        if (raw) {
          const value = JSON.parse(raw);
          if (
            value.design &&
            value.baseVersion === (server?.version || 0) &&
            !sameData(value.design, server?.design || fresh())
          )
            setRecovery(value);
        }
      } catch (e) {
        if (alive) setError(e);
      } finally {
        if (alive) setInitialized(true);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);
  useEffect(() => {
    if (!initialized) return;
    try {
      const key = `bespoke-recovery:${brief?.id || "new"}`;
      if (dirty)
        sessionStorage.setItem(
          key,
          JSON.stringify({
            design: d,
            baseVersion: brief?.version || 0,
            id: brief?.id || null,
          }),
        );
      else if (!recovery) sessionStorage.removeItem(key);
    } catch {
      setNotice(
        "Tab recovery is unavailable. Save your draft to keep these changes.",
      );
    }
  }, [d, brief, dirty, initialized, recovery]);
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (dirty || mediaBusy) e.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, mediaBusy]);
  function change(next: Design) {
    setD(next);
    setNotice("");
    setAgreed(false);
  }
  function field<K extends keyof Design>(key: K, value: Design[K]) {
    change({ ...d, [key]: value });
  }
  function navigate(n: number) {
    if (mediaBusy) {
      setError(Error("Finish recording or uploading before changing steps."));
      return;
    }
    if (n > 0 && !d.fabric) {
      setError(Error("Choose a fabric to start your design."));
      return;
    }
    if (n > 1 && !d.lace_choice) {
      setError(Error("Choose a lace, select without lace, or ask for help."));
      return;
    }
    setStep(n);
    setError(null);
    window.scrollTo({ top: 0, behavior: "instant" });
    requestAnimationFrame(() => title.current?.focus());
  }
  async function ensureBrief() {
    if (record.current) return record.current;
    const b = await api<Brief>("/bespoke", json("POST"));
    record.current = b;
    setBrief(b);
    window.history.replaceState(null, "", `/bespoke?design=${b.id}`);
    sessionStorage.removeItem("bespoke-recovery:new");
    return b;
  }
  function downloadDraft() {
    const blob = new Blob(
      [
        JSON.stringify(
          { briefId: brief?.id, baseVersion: brief?.version, design: d },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "MyShoppe-design-backup.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function reloadSaved() {
    if (!brief) return;
    const b = await api<Brief>(`/bespoke/${brief.id}`);
    setBrief(b);
    setD(b.design);
    setAgreed(false);
    setReloadConfirm(false);
    setNotice("Latest brief loaded.");
  }
  async function save() {
    const b = await ensureBrief();
    const updated = await api<Brief>(
      `/bespoke/${b.id}`,
      json("PUT", { expected_version: b.version, design: current.current }),
    );
    record.current = updated;
    setBrief(updated);
    return updated;
  }
  async function run(fn: () => Promise<void>) {
    if (locked.current) return;
    locked.current = true;
    setPending(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e);
      requestAnimationFrame(() =>
        document
          .querySelector(".studio-feedback")
          ?.scrollIntoView({ block: "center" }),
      );
    } finally {
      locked.current = false;
      setPending(false);
    }
  }
  async function action(action: "submit" | "agree") {
    await run(async () => {
      const b = await save();
      const updated = await api<Brief>(
        `/bespoke/${b.id}/actions`,
        json("POST", { expected_version: b.version, action }),
      );
      setBrief(updated);
      setNotice(
        action === "submit"
          ? "Your design is with the boutique. Return here for the review."
          : "Your agreement is recorded. The boutique can now release the brief to masterji.",
      );
    });
  }
  async function upload(file: File) {
    if (file.size > 5_000_000) throw Error("Use a file under 5 MB.");
    const b = await ensureBrief();
    const form = new FormData();
    form.append("file", file);
    const result = await api<{ id: string }>(`/bespoke/${b.id}/assets`, {
      method: "POST",
      body: form,
    });
    return result.id;
  }
  const label = [
    "YOUR IDEAS.\nOUR HANDS.",
    "THE FINISHING\nTOUCH.",
    "YOUR KIND\nOF YOU.",
    "EVERY DETAIL.\nONE BRIEF.",
  ][step];
  const all = fabrics.filter(
    (m) =>
      (filter === "All" || m.category === filter) &&
      `${m.name} ${m.description}`.toLowerCase().includes(query.toLowerCase()),
  );
  function tiles(items: Material[], multiple = false) {
    return (
      <div className={`material-grid ${multiple ? "lace-grid" : ""}`}>
        {items.map((m, i) => {
          const active = multiple ? d.laces.includes(m.id) : d.fabric === m.id;
          return (
            <article
              className={`material-card ${active ? "is-selected" : ""}`}
              key={m.id}
            >
              <button
                className="material-select"
                aria-pressed={active}
                aria-label={`Select ${m.name}`}
                onClick={() =>
                  multiple
                    ? change({
                        ...d,
                        laces: active
                          ? d.laces.filter((x) => x !== m.id)
                          : [...d.laces, m.id],
                        lace_choice:
                          active && d.laces.length === 1 ? "" : "selected",
                      })
                    : field("fabric", m.id)
                }
              >
                <div className="material-photo">
                  <img
                    src={asset(m.id)}
                    srcSet={`${asset(m.id, 360)} 360w, ${asset(m.id)} 640w, ${asset(m.id, 1280)} 1280w`}
                    sizes="(max-width: 767px) 45vw, (max-width: 1279px) 30vw, 24vw"
                    alt={m.description}
                    width="640"
                    height="640"
                    loading="lazy"
                  />
                  <span className="material-number">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="material-check">{active ? "✓" : "+"}</span>
                </div>
                <div className="material-caption">
                  <h3>{m.name}</h3>
                  <p>{m.description}</p>
                  <span>{active ? "SELECTED" : "SELECT"}</span>
                </div>
              </button>
              <button
                className="texture-zoom"
                aria-label={`View ${m.name} close-up`}
                onClick={() => setZoom(m)}
              >
                ↗ <span>View texture</span>
              </button>
            </article>
          );
        })}
      </div>
    );
  }
  return (
    <main id="main" className="bespoke-studio">
      <div className="studio-topline">
        <Link href="/">MYSHOPPE / THE BESPOKE STUDIO</Link>
        <div>
          <button
            disabled={pending || mediaBusy}
            onClick={() =>
              void run(async () => {
                if (dirty) {
                  await save();
                  setNotice("Draft saved before opening your designs.");
                }
                setSaved(await api<Brief[]>("/bespoke"));
                setLibrary(true);
              })
            }
          >
            MY DESIGNS ↗
          </button>
          <button
            disabled={pending || mediaBusy || !initialized}
            onClick={() =>
              void run(async () => {
                await save();
                setNotice("Draft saved to your MyShoppe session.");
              })
            }
          >
            {pending ? "SAVING…" : "SAVE DRAFT"}
          </button>
        </div>
      </div>
      <nav className="studio-steps" aria-label="Design steps">
        {["Fabric", "Lace", "Your design", "The brief"].map((s, i) => (
          <button
            key={s}
            onClick={() => navigate(i)}
            disabled={pending || mediaBusy}
            aria-current={step === i ? "step" : undefined}
          >
            <span>0{i + 1}</span>
            {s}
            <small>{i < step ? "✓" : ""}</small>
          </button>
        ))}
      </nav>
      <div className={`studio-intro ${step === 0 ? "studio-hero" : ""}`}>
        <div>
          <p className="studio-kicker">
            {
              [
                "A FABRIC. A FEELING. A CONVERSATION.",
                "SMALL DETAILS, PERSONAL CHOICES",
                "NO DESIGN VOCABULARY NEEDED",
                "FROM AN IDEA TO A SHARED UNDERSTANDING",
              ][step]
            }
          </p>
          <h1 ref={title} tabIndex={-1}>
            {label}
          </h1>
          <p className="studio-lead">
            {
              [
                "Start with a fabric you love. Add the little details. Together, we’ll make something that feels like you.",
                "Choose a border, mix a few, or let the fabric speak for itself. Every little detail has its place.",
                "The neckline from one photo. The sleeves from another. Bring them together, in your own words.",
                "Review the materials, fit and finishing touches. One shared template, from your first idea to masterji’s worktable.",
              ][step]
            }
          </p>
          {step === 0 && (
            <span className="studio-signature">Made with you.</span>
          )}
        </div>
        {step === 0 && (
          <figure className="atelier-photo">
            <img
              src={asset("atelier-hero", 1280)}
              srcSet={`${asset("atelier-hero")} 640w, ${asset("atelier-hero", 1280)} 1280w`}
              sizes="(max-width:767px) 100vw, 50vw"
              width="1280"
              height="850"
              alt="Embroidered fabric, lace and dressmaking tools on an atelier table"
              fetchPriority="high"
            />
            <figcaption>THE STUDIO / FROM THE FIRST THREAD</figcaption>
          </figure>
        )}
      </div>
      <div className="studio-feedback">
        <ErrorMessage error={error} />
        {notice && <p role="status">{notice}</p>}
        <span>
          {dirty
            ? "Unsaved changes · recovery kept in this tab"
            : brief
              ? `${statusLabel[brief.status]} · Revision ${brief.version}`
              : "Your story starts here"}
        </span>
        {brief && (
          <button
            disabled={pending || mediaBusy}
            onClick={() =>
              void run(async () => {
                if (dirty) {
                  setReloadConfirm(true);
                  return;
                }
                await reloadSaved();
              })
            }
          >
            Refresh status ↻
          </button>
        )}
      </div>
      <fieldset className="studio-edit-area" disabled={pending || !initialized}>
        {step === 0 && (
          <section>
            <div className="studio-section-heading">
              <div>
                <p className="studio-kicker">01 / THE MATERIAL LIBRARY</p>
                <h2>Find your fabric.</h2>
                <p>Ten textures. A world of possibilities.</p>
              </div>
              <label className="fabric-search">
                Search fabrics
                <input
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Try ivory, floral, woven…"
                />
              </label>
            </div>
            <div className="fabric-toolbar">
              <div>
                {["All", "Plain", "Embroidered", "Textured"].map((f) => (
                  <button
                    key={f}
                    aria-pressed={filter === f}
                    onClick={() => setFilter(f)}
                  >
                    {f}
                  </button>
                ))}
              </div>
              <span>{all.length} FABRICS</span>
            </div>
            {tiles(all)}
            {!all.length && (
              <div className="studio-empty">
                <h3>No fabrics match.</h3>
                <button
                  className="button"
                  onClick={() => {
                    setFilter("All");
                    setQuery("");
                  }}
                >
                  CLEAR FILTERS
                </button>
              </div>
            )}
            <p className="material-disclaimer">
              Illustrative studio collection · generated texture references. The
              boutique will confirm actual fabric, colour, composition,
              availability and price.
            </p>
          </section>
        )}
        {step === 1 && (
          <section>
            {selected && (
              <div className="pairing-preview">
                <img
                  src={asset(selected.id)}
                  alt={selected.name}
                  width="640"
                  height="640"
                />
                <div>
                  <span className="studio-kicker">YOUR MATERIAL PALETTE</span>
                  <h2>{selected.name}</h2>
                  <p>
                    {d.laces.length
                      ? "A pairing to explore together."
                      : "Choose a lace below to see your materials together."}
                  </p>
                  <div className="pairing-laces">
                    {d.laces.map((id) => (
                      <figure key={id}>
                        <img
                          src={asset(id, 360)}
                          alt={material(id)?.name}
                          width="120"
                          height="120"
                        />
                        <figcaption>{material(id)?.name}</figcaption>
                      </figure>
                    ))}
                  </div>
                  <button className="text-button" onClick={() => navigate(0)}>
                    Change fabric ↗
                  </button>
                </div>
              </div>
            )}
            <div className="studio-section-heading">
              <div>
                <p className="studio-kicker">02 / FINISHING TOUCHES</p>
                <h2>Find the little extra.</h2>
              </div>
              <p>Select one or more lace options.</p>
            </div>
            {tiles(laces, true)}
            <div className="studio-actions lace-alternatives">
              {(
                [
                  ["none", "Keep it without lace"],
                  ["help", "Help me choose"],
                ] as const
              ).map(([v, t]) => (
                <button
                  className="button"
                  key={v}
                  aria-pressed={d.lace_choice === v}
                  onClick={() => change({ ...d, laces: [], lace_choice: v })}
                >
                  {t}
                </button>
              ))}
            </div>
            <div className="studio-form-grid">
              <label className="field">
                Lace placement
                <textarea
                  maxLength={2000}
                  value={d.placement}
                  onChange={(e) => field("placement", e.target.value)}
                  placeholder="A fine edge on the sleeves and dupatta. Keep the neckline plain."
                />
              </label>
              <label className="field">
                Fabric / lace quantity (optional)
                <input
                  value={d.quantity}
                  maxLength={2000}
                  onChange={(e) => field("quantity", e.target.value)}
                  placeholder="If known, include units. Otherwise we’ll confirm."
                />
              </label>
            </div>
            <p className="material-disclaimer">
              Pairings are illustrative references, subject to actual material
              confirmation.
            </p>
          </section>
        )}
        {step === 2 && (
          <section>
            <div className="studio-form-grid customer-fields">
              <label className="field">
                Your name *
                <input
                  autoComplete="name"
                  value={d.name}
                  maxLength={100}
                  onChange={(e) => field("name", e.target.value)}
                />
              </label>
              <label className="field">
                Occasion
                <input
                  value={d.occasion}
                  maxLength={200}
                  placeholder="A celebration, everyday, something special…"
                  onChange={(e) => field("occasion", e.target.value)}
                />
              </label>
              <label className="field">
                Requested date
                <input
                  type="date"
                  value={d.requested_date || ""}
                  onChange={(e) =>
                    field("requested_date", e.target.value || null)
                  }
                />
                <small>The boutique will confirm timing.</small>
              </label>
            </div>
            <div className="idea-layout">
              <DesignBoard
                design={d}
                onChange={change}
                upload={upload}
                busy={pending}
                onError={setError}
                onActive={setMediaBusy}
              />
              <div className="idea-template">
                <p className="studio-kicker">YOUR DESIGN TEMPLATE</p>
                <h2>Make it yours.</h2>
                <label className="field">
                  The idea, in your own words *
                  <textarea
                    value={d.vision}
                    maxLength={2000}
                    rows={5}
                    onChange={(e) => field("vision", e.target.value)}
                    placeholder="An easy, flowing kurta for a family lunch. I love the neckline in my first photo…"
                  />
                </label>
                {designFields.map(([key, label, options]) => (
                  <label className="field" key={key}>
                    {label}
                    {key === "silhouette" ? " *" : ""}
                    <select
                      aria-label={label}
                      value={d[key]}
                      onChange={(e) => field(key, e.target.value)}
                    >
                      <option value="">Choose or confirm together</option>
                      {options.map((o) => (
                        <option key={o}>{o}</option>
                      ))}
                    </select>
                  </label>
                ))}
                <label className="field">
                  Fit preference
                  <input
                    value={d.fit}
                    maxLength={2000}
                    onChange={(e) => field("fit", e.target.value)}
                    placeholder="Relaxed through the waist, fitted shoulders…"
                  />
                </label>
                <details className="fit-details">
                  <summary>Measurements & fitting plan</summary>
                  <label className="field">
                    Measurement units
                    <select
                      value={d.units}
                      onChange={(e) =>
                        field("units", e.target.value as "cm" | "in")
                      }
                    >
                      <option value="cm">Centimetres (cm)</option>
                      <option value="in">Inches (in)</option>
                    </select>
                  </label>
                  <label className="field">
                    Measurements (optional)
                    <textarea
                      value={d.measurements}
                      maxLength={2000}
                      onChange={(e) => field("measurements", e.target.value)}
                      placeholder="Label each measurement: bust, waist, hip, shoulder, sleeve, garment length."
                    />
                  </label>
                  <label className="field">
                    Fitting plan
                    <textarea
                      value={d.fitting_plan}
                      maxLength={2000}
                      onChange={(e) => field("fitting_plan", e.target.value)}
                      placeholder="Measure at the boutique, bring a well-fitting garment…"
                    />
                  </label>
                </details>
              </div>
            </div>
          </section>
        )}
      </fieldset>
      {step === 3 && (
        <section className="studio-review-layout">
          <MasterBrief design={d} brief={dirty ? null : brief} />
          <aside className="brief-aside">
            <p className="studio-kicker">THE NEXT STITCH</p>
            <h2>
              {brief && !dirty ? statusLabel[brief.status] : "Ready to share?"}
            </h2>
            <p>
              Your boutique will review materials, measurements and instructions
              before you agree to the final brief.
            </p>
            {(!brief || dirty || brief.status === "draft") && (
              <>
                <p>
                  Required: fabric, lace choice, your name, design idea and
                  silhouette.
                </p>
                <button
                  className="button primary"
                  disabled={pending || mediaBusy}
                  onClick={() => void action("submit")}
                >
                  {pending ? "SENDING…" : "SEND TO BOUTIQUE →"}
                </button>
              </>
            )}
            {brief?.status === "submitted" && !dirty && (
              <p role="status">
                Submitted. Use Refresh status to check for the boutique’s
                review.
              </p>
            )}
            {brief?.status === "reviewing" && !dirty && (
              <>
                <p>
                  {brief.review.questions
                    ? "The boutique has questions. Update your design to answer them, then resubmit."
                    : "Read the confirmed materials, fit and stitching instructions before agreeing."}
                </p>
                <label className="agreement-check">
                  <input
                    type="checkbox"
                    checked={agreed}
                    onChange={(e) => setAgreed(e.target.checked)}
                  />
                  I agree to this revision’s materials, fit and stitching
                  instructions.
                </label>
                <button
                  className="button primary"
                  disabled={
                    !agreed ||
                    pending ||
                    !!brief.review.questions ||
                    !brief.review.materials ||
                    !brief.review.measurements
                  }
                  onClick={() => void action("agree")}
                >
                  AGREE TO THIS BRIEF
                </button>
              </>
            )}
            <button className="button" onClick={() => window.print()}>
              PRINT / SAVE PDF ↗
            </button>
            <p className="small">
              Only a brief marked “Ready for masterji” is released for cutting
              and stitching.
            </p>
            {brief && (
              <details>
                <summary>Revision history ({brief.history.length})</summary>
                <ol className="revision-history">
                  {[...brief.history].reverse().map((h) => (
                    <li key={h.version}>
                      Revision {h.version} · {h.status}
                      <br />
                      <small>{new Date(h.at).toLocaleString("en-IN")}</small>
                    </li>
                  ))}
                </ol>
              </details>
            )}
            <Link href="/account">
              {shop.session?.email
                ? "Your account ↗"
                : "Sign in to keep designs across devices ↗"}
            </Link>
          </aside>
        </section>
      )}
      <div className="studio-bottom-bar">
        <div>
          {selected && (
            <img src={asset(selected.id, 360)} alt="" width="48" height="48" />
          )}
          <div>
            <b>{selected?.name || "Every story starts with a fabric."}</b>
            <span>
              {d.laces.map((id) => material(id)?.name).join(" + ") ||
                (d.lace_choice === "none"
                  ? "Without lace"
                  : d.lace_choice === "help"
                    ? "Choose with the boutique"
                    : "Your ideas, our craft.")}
            </span>
          </div>
        </div>
        <div>
          {step > 0 && (
            <button
              className="text-button"
              disabled={pending || mediaBusy}
              onClick={() => navigate(step - 1)}
            >
              ← Back
            </button>
          )}
          {step < 3 && (
            <button
              className="button primary"
              disabled={pending || mediaBusy}
              onClick={() => navigate(step + 1)}
            >
              {
                ["CHOOSE YOUR LACE", "CREATE YOUR DESIGN", "REVIEW YOUR BRIEF"][
                  step
                ]
              }{" "}
              →
            </button>
          )}
          {step === 3 && (
            <button
              className="button"
              disabled={pending || mediaBusy}
              onClick={() => navigate(2)}
            >
              EDIT DESIGN
            </button>
          )}
        </div>
      </div>
      <Dialog
        open={!!zoom}
        onClose={() => setZoom(null)}
        title="Fabric and lace close-up"
        className="texture-dialog"
      >
        {zoom && (
          <>
            <img
              src={asset(zoom.id, 1280)}
              alt={`${zoom.name}: ${zoom.description}`}
              width="1280"
              height="1280"
            />
            <h2>{zoom.name}</h2>
            <p>{zoom.description} · Illustrative texture reference</p>
            <button
              className="button primary"
              onClick={() => {
                if (zoom.id.startsWith("fabric")) field("fabric", zoom.id);
                else
                  change({
                    ...d,
                    laces: [...new Set([...d.laces, zoom.id])],
                    lace_choice: "selected",
                  });
                setZoom(null);
              }}
            >
              SELECT {zoom.id.startsWith("fabric") ? "FABRIC" : "LACE"}
            </button>
          </>
        )}
      </Dialog>
      <Dialog
        open={library}
        onClose={() => setLibrary(false)}
        title="Your saved designs"
      >
        <h2>Your design stories.</h2>
        <a className="button" href="/bespoke">
          START A NEW DESIGN +
        </a>
        {!saved.length && <p>No saved designs yet.</p>}
        <div className="saved-designs">
          {saved.map((b) => (
            <a href={`/bespoke?design=${b.id}`} key={b.id}>
              {b.design.fabric && (
                <img
                  src={asset(b.design.fabric, 360)}
                  alt=""
                  width="80"
                  height="80"
                />
              )}
              <div>
                <b>
                  {b.design.name || "Untitled design"}{" "}
                  {b.design.occasion && `/ ${b.design.occasion}`}
                </b>
                <p>
                  {statusLabel[b.status]} · Revision {b.version}
                </p>
              </div>
              <span>↗</span>
            </a>
          ))}
        </div>
      </Dialog>
      <Dialog
        open={reloadConfirm}
        onClose={() => setReloadConfirm(false)}
        title="Reload saved brief"
      >
        <h2>Keep a copy before reloading.</h2>
        <p>
          Your unsaved changes differ from the saved brief. Download a backup if
          you want to keep your notes.
        </p>
        <div className="studio-actions">
          <button className="button" onClick={downloadDraft}>
            DOWNLOAD MY CHANGES
          </button>
          <button
            className="button primary"
            disabled={pending}
            onClick={() => void run(reloadSaved)}
          >
            DISCARD CHANGES & RELOAD
          </button>
        </div>
      </Dialog>
      <Dialog
        open={!!recovery}
        onClose={() => setRecovery(null)}
        title="Recover unsaved changes"
      >
        <h2>Pick up where you left off.</h2>
        <p>This tab has unsaved changes from this revision.</p>
        <button
          className="button primary"
          onClick={() => {
            if (recovery) setD(recovery.design);
            setRecovery(null);
          }}
        >
          RESTORE CHANGES
        </button>
        <button className="button" onClick={() => setRecovery(null)}>
          USE SAVED VERSION
        </button>
      </Dialog>
    </main>
  );
}
