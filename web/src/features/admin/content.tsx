"use client";
import { ErrorMessage } from "@/components/ui";
import {
  api,
  json,
  titleCase,
  type Block,
  type Campaign,
  type Department,
} from "@/lib/api";
import { useEffect, useState } from "react";

export function CampaignEditor() {
  const [department, setDepartment] = useState<Department>("women");
  const [history, setHistory] = useState<Campaign[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(false);
  const [uploading, setUploading] = useState<number | null>(null);
  async function uploadMedia(index: number, file: File) {
    setUploading(index);
    setError(null);
    try {
      const body = new FormData();
      body.set("file", file);
      const video = blocks[index].type === "video";
      const result = await api<{
        src: string;
        poster?: string;
        job_key?: string;
      }>(video ? "/admin/media/video" : "/admin/media", {
        method: "POST",
        body,
      });
      if (result.job_key) {
        let ready = false;
        for (let attempt = 0; attempt < 150; attempt++) {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          const job = await api<{ status: string; last_error: string }>(
            `/admin/media/jobs/${encodeURIComponent(result.job_key)}`,
          );
          if (job.status === "done") {
            ready = true;
            break;
          }
          if (job.status === "failed")
            throw new Error(
              "Video processing failed. Use a valid film under 60 seconds.",
            );
        }
        if (!ready)
          throw new Error(
            "Video is still processing. Check the worker and try again later.",
          );
      }
      setBlocks((old) =>
        old.map((block, i) =>
          i === index
            ? {
                ...block,
                src: result.src,
                poster: result.poster || block.poster,
              }
            : block,
        ),
      );
    } catch (e) {
      setError(e);
    } finally {
      setUploading(null);
    }
  }
  const load = async () => {
    const data = await api<Campaign[]>(`/admin/campaigns/${department}`);
    setHistory(data);
    setBlocks(data[0]?.content.blocks || []);
  };
  useEffect(() => {
    load().catch(setError);
  }, [department]);
  const change = (index: number, key: keyof Block, value: string) =>
    setBlocks((b) =>
      b.map((block, i) => (i === index ? { ...block, [key]: value } : block)),
    );
  async function save() {
    setBusy(true);
    try {
      await api(
        `/admin/campaigns/${department}`,
        json("POST", { expected_revision: history[0]?.revision || 0, blocks }),
      );
      await load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="admin-title">
        <h1>Campaign studio</h1>
        <select
          aria-label="Campaign department"
          value={department}
          disabled={uploading !== null || busy}
          onChange={(e) => setDepartment(e.target.value as Department)}
        >
          <option value="women">Women</option>
          <option value="home">Home</option>
        </select>
      </div>
      <p className="muted">
        One sequence: hero → film → posters → collection. Drafts do not change
        the live storefront.
      </p>
      <ErrorMessage error={error} />
      <div className="campaign-editor">
        {blocks.map((b, i) => (
          <section className="admin-panel campaign-block-editor" key={i}>
            <div className="block-number">
              {String(i + 1).padStart(2, "0")}
              <span>{b.type}</span>
            </div>
            {b.type === "video" ? (
              <video
                src={b.src}
                poster={b.poster || undefined}
                controls
                muted
              />
            ) : (
              b.src && <img src={b.src} alt="Campaign preview" />
            )}
            <div>
              {b.type !== "collection-entry" && (
                <label className="upload-area">
                  {uploading === i
                    ? "PROCESSING MEDIA…"
                    : b.type === "video"
                      ? "UPLOAD FILM (MAX 60 SECONDS / 80 MB)"
                      : "UPLOAD IMAGE"}
                  <input
                    type="file"
                    accept={
                      b.type === "video"
                        ? "video/*"
                        : "image/jpeg,image/png,image/webp"
                    }
                    disabled={uploading !== null}
                    onChange={(e) => {
                      if (e.target.files?.[0])
                        uploadMedia(i, e.target.files[0]);
                    }}
                  />
                </label>
              )}
              {(
                [
                  "title",
                  "subtitle",
                  "src",
                  "mobile_src",
                  "poster",
                  "target",
                ] as const
              ).map((k) => (
                <label className="field" key={k}>
                  {titleCase(k)}
                  <input
                    value={b[k] || ""}
                    onChange={(e) => change(i, k, e.target.value)}
                  />
                </label>
              ))}
              <label className="field">
                Treatment
                <select
                  value={b.layout}
                  onChange={(e) => change(i, "layout", e.target.value)}
                >
                  {["full", "split", "inset"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                Overlay tone
                <select
                  value={b.tone}
                  onChange={(e) => change(i, "tone", e.target.value)}
                >
                  <option>dark</option>
                  <option>light</option>
                </select>
              </label>
            </div>
          </section>
        ))}
      </div>
      <div className="editor-actions">
        <button
          className="button primary"
          disabled={busy || uploading !== null}
          onClick={save}
        >
          SAVE DRAFT
        </button>
        <button className="button" onClick={() => setPreview(!preview)}>
          {preview ? "CLOSE" : "OPEN"} SAVED DRAFT PREVIEW
        </button>
      </div>
      {preview && (
        <iframe
          className="campaign-preview"
          title="Saved campaign draft preview"
          src={`/preview/campaign?department=${department}&revision=${history[0]?.id}`}
        />
      )}
      <section className="admin-panel">
        <h2>Revision history</h2>
        {history.map((h) => (
          <div className="revision-row" key={h.id}>
            <span>
              VERSION {h.revision} {h.published ? " / LIVE" : " / SAVED"}
            </span>
            <button
              className="button"
              disabled={h.published || busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await api(
                    `/admin/campaign-revisions/${h.id}/publish`,
                    json("POST"),
                  );
                  await load();
                } catch (e) {
                  setError(e);
                } finally {
                  setBusy(false);
                }
              }}
            >
              {h.revision === history[0]?.revision
                ? "PUBLISH"
                : "RESTORE THIS VERSION"}
            </button>
          </div>
        ))}
      </section>
    </>
  );
}
