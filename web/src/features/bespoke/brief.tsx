"use client";
import {
  asset,
  material,
  referenceSrc,
  statusLabel,
  type Brief,
  type Design,
  type Review,
} from "./data";

const text = (value?: string | null) => value?.trim() || "To confirm";
export function MasterBrief({
  design: d,
  brief,
  review: override,
  historical = false,
}: {
  design: Design;
  brief: Brief | null;
  review?: Review;
  historical?: boolean;
}) {
  const r = override || brief?.review || {};
  const materials = [d.fabric, ...d.laces].map(material).filter((x) => !!x);
  return (
    <article className="master-brief" id="masterji-brief">
      <header className="brief-heading">
        <div>
          <span className="studio-kicker">MYSHOPPE / BESPOKE STUDIO</span>
          <h2>The stitching brief.</h2>
        </div>
        <div>
          <strong>
            {brief
              ? `MS-${brief.id.slice(0, 8).toUpperCase()}`
              : "UNSAVED DRAFT"}
          </strong>
          <p>
            Revision {brief?.version || "—"} ·{" "}
            {brief ? statusLabel[brief.status] : "Draft"}
          </p>
        </div>
      </header>
      <p className="brief-warning">
        {historical
          ? "HISTORICAL SNAPSHOT · Not the current production brief."
          : brief?.status === "ready"
            ? "Approved handoff · work from this revision. Confirm any changes with the boutique."
            : "WORK IN PROGRESS · Not released for cutting or stitching."}
      </p>
      <section>
        <h3>01 / Customer & occasion</h3>
        <dl className="brief-grid">
          <div>
            <dt>Customer</dt>
            <dd>{text(d.name)}</dd>
          </div>
          <div>
            <dt>Occasion</dt>
            <dd>{text(d.occasion)}</dd>
          </div>
          <div>
            <dt>Requested date</dt>
            <dd>
              {d.requested_date
                ? new Date(`${d.requested_date}T12:00:00`).toLocaleDateString(
                    "en-IN",
                  )
                : "To confirm"}{" "}
              <small>Subject to boutique confirmation</small>
            </dd>
          </div>
        </dl>
      </section>
      <section>
        <h3>02 / Materials & placement</h3>
        <div className="brief-materials">
          {materials.map((m) => (
            <figure key={m.id}>
              <img src={asset(m.id)} alt={m.name} width="120" height="120" />
              <figcaption>{m.name}</figcaption>
            </figure>
          ))}
        </div>
        <p>
          Illustrative material references. Final fabric, colour, trim and
          quantity require boutique confirmation.
        </p>
        <dl className="brief-grid">
          <div>
            <dt>Lace choice</dt>
            <dd>
              {d.lace_choice === "none"
                ? "Without lace"
                : d.lace_choice === "help"
                  ? "Help requested"
                  : materials
                      .slice(1)
                      .map((m) => m.name)
                      .join(", ") || "To confirm"}
            </dd>
          </div>
          <div>
            <dt>Requested quantity</dt>
            <dd>{text(d.quantity)}</dd>
          </div>
          <div>
            <dt>Lace placement</dt>
            <dd>{text(d.placement)}</dd>
          </div>
          <div className="brief-wide">
            <dt>Boutique material confirmation</dt>
            <dd>{text(r.materials)}</dd>
          </div>
        </dl>
      </section>
      <section>
        <h3>03 / Garment specification</h3>
        <p className="brief-vision">{text(d.vision)}</p>
        <dl className="brief-grid">
          {(
            [
              "silhouette",
              "neckline",
              "sleeves",
              "length",
              "bottom",
              "dupatta",
            ] as const
          ).map((k) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{text(d[k])}</dd>
            </div>
          ))}
        </dl>
      </section>
      <section>
        <h3>04 / Fit & measurements</h3>
        <dl className="brief-grid">
          <div>
            <dt>Fit preference</dt>
            <dd>{text(d.fit)}</dd>
          </div>
          <div>
            <dt>Measurements ({d.units})</dt>
            <dd>{text(d.measurements)}</dd>
          </div>
          <div>
            <dt>Fitting plan</dt>
            <dd>{text(d.fitting_plan)}</dd>
          </div>
          <div className="brief-wide">
            <dt>Boutique fit confirmation</dt>
            <dd>{text(r.measurements)}</dd>
          </div>
        </dl>
      </section>
      <section>
        <h3>05 / References & detail notes</h3>
        {!d.references.length && <p>No photo references added.</p>}
        <div className="brief-references">
          {d.references.map((ref, i) => (
            <figure key={ref.asset_id}>
              <div className="pinned-image">
                <img
                  src={referenceSrc(ref.asset_id)}
                  alt={ref.name}
                  width="400"
                  height="400"
                />
                {ref.pins.map((p, n) => (
                  <span
                    className="detail-pin"
                    key={n}
                    style={{ left: `${p.x}%`, top: `${p.y}%` }}
                  >
                    {n + 1}
                  </span>
                ))}
              </div>
              <figcaption>
                Reference {i + 1} / {ref.name}
              </figcaption>
              <ol>
                {ref.pins.map((p, n) => (
                  <li key={n}>
                    <b>{p.part}:</b> {p.note}
                  </li>
                ))}
              </ol>
            </figure>
          ))}
        </div>
        {d.voice_id && (
          <div className="voice-reference">
            <p>
              Voice note attached. Confirm all production instructions in
              writing below.
            </p>
            <audio controls src={referenceSrc(d.voice_id)} />
          </div>
        )}
      </section>
      <section>
        <h3>06 / Confirmed stitching instructions</h3>
        <p className="preserve-lines">{text(r.instructions)}</p>
        <h4>Open questions</h4>
        <p className="preserve-lines">
          {r.questions?.trim() || "No open questions recorded."}
        </p>
      </section>
      <section>
        <h3>07 / Agreement & handoff</h3>
        <dl className="brief-grid">
          <div>
            <dt>Customer agreement</dt>
            <dd>
              {brief?.agreement
                ? `${brief.agreement.name} · review revision ${brief.agreement.version} · ${new Date(brief.agreement.at).toLocaleString("en-IN")}`
                : "Awaiting customer agreement"}
            </dd>
          </div>
          <div>
            <dt>Boutique review</dt>
            <dd>
              {r.at
                ? `${r.reviewed_by || "Boutique owner"} · ${new Date(r.at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}`
                : "Awaiting owner review"}
            </dd>
          </div>
          <div>
            <dt>Release to masterji</dt>
            <dd>
              {historical
                ? "HISTORICAL SNAPSHOT · Not the current production brief."
                : brief?.status === "ready"
                  ? `Released · revision ${brief.version}`
                  : "Not released"}
            </dd>
          </div>
        </dl>
      </section>
      <footer>
        MYSHOPPE · Keep this brief with the garment. Any change requires a
        revised brief and renewed agreement.
      </footer>
    </article>
  );
}
