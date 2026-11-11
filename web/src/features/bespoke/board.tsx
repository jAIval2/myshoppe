"use client";
import { useEffect, useRef, useState } from "react";
import { Dialog } from "@/components/ui";
import {
  referenceSrc,
  studioReferences,
  asset,
  type Design,
  type Pin,
} from "./data";

export function DesignBoard({
  design: d,
  onChange,
  upload,
  busy,
  onError,
  onActive,
}: {
  design: Design;
  onChange: (d: Design) => void;
  upload: (file: File) => Promise<string>;
  busy: boolean;
  onError: (e: unknown) => void;
  onActive: (active: boolean) => void;
}) {
  const [pin, setPin] = useState<{
    index: number;
    x: number;
    y: number;
  } | null>(null);
  const [referenceLibrary, setReferenceLibrary] = useState(false);
  const [part, setPart] = useState("Neckline"),
    [note, setNote] = useState("");
  const [recording, setRecording] = useState(false),
    [seconds, setSeconds] = useState(0),
    [uploading, setUploading] = useState(false);
  useEffect(() => {
    onActive(recording || uploading);
    return () => onActive(false);
  }, [recording, uploading, onActive]);
  const recorder = useRef<MediaRecorder | null>(null),
    stream = useRef<MediaStream | null>(null);
  const mounted = useRef(true),
    current = useRef(d);
  current.current = d;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      stream.current?.getTracks().forEach((t) => t.stop());
      if (recorder.current?.state === "recording") recorder.current.stop();
    };
  }, []);
  useEffect(() => {
    if (!recording) return;
    const t = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [recording]);
  useEffect(() => {
    if (seconds >= 120 && recorder.current?.state === "recording")
      recorder.current.stop();
  }, [seconds]);
  const addPhotos = async (files: FileList | null) => {
    if (!files) return;
    setUploading(true);
    try {
      for (const f of Array.from(files)) {
        if (current.current.references.length >= 6)
          throw Error(
            "You can keep up to six references. Remove one before adding another.",
          );
        const id = await upload(f);
        onChange({
          ...current.current,
          references: [
            ...current.current.references,
            { asset_id: id, name: f.name.slice(0, 120), pins: [] },
          ],
        });
      }
    } catch (e) {
      onError(e);
    } finally {
      setUploading(false);
    }
  };
  async function record() {
    if (recording) {
      recorder.current?.stop();
      return;
    }
    setUploading(true);
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder)
        throw Error(
          "Voice recording is unavailable here. Add your idea in writing instead.",
        );
      const audio = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mounted.current) {
        audio.getTracks().forEach((t) => t.stop());
        return;
      }
      stream.current = audio;
      const type = ["audio/webm", "audio/mp4", "audio/ogg"].find((t) =>
        MediaRecorder.isTypeSupported(t),
      );
      const rec = new MediaRecorder(
        audio,
        type ? { mimeType: type } : undefined,
      );
      recorder.current = rec;
      const chunks: Blob[] = [];
      rec.ondataavailable = (e) => {
        if (e.data.size) chunks.push(e.data);
      };
      rec.onstop = async () => {
        audio.getTracks().forEach((t) => t.stop());
        if (!mounted.current) return;
        setRecording(false);
        setUploading(true);
        try {
          const file = new File(chunks, "voice-note", { type: rec.mimeType });
          const id = await upload(file);
          if (mounted.current) onChange({ ...current.current, voice_id: id });
        } catch (e) {
          onError(e);
        } finally {
          if (mounted.current) setUploading(false);
        }
      };
      rec.start();
      setSeconds(0);
      setRecording(true);
      setUploading(false);
    } catch (e) {
      stream.current?.getTracks().forEach((t) => t.stop());
      setUploading(false);
      onError(e);
    }
  }
  return (
    <div className="design-board">
      <div className="studio-section-heading">
        <div>
          <span className="studio-kicker">YOUR REFERENCE BOARD</span>
          <h3>
            A neckline here.
            <br />A little detail there.
          </h3>
        </div>
        <span>{d.references.length} / 6</span>
      </div>
      <p>
        Bring together the parts you love. Tap a photo to pin a detail, or use
        Add detail below it.
      </p>
      <div className="studio-actions">
        <label className="button">
          <span>{uploading ? "UPLOADING…" : "+ ADD PHOTOS"}</span>
          <input
            className="visually-hidden"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            disabled={busy || uploading || recording}
            onChange={(e) => {
              void addPhotos(e.target.files);
              e.target.value = "";
            }}
          />
        </label>
        <button
          className="text-button"
          disabled={d.references.length >= 6 || uploading || recording}
          onClick={() => setReferenceLibrary(true)}
        >
          Use studio reference ↗
        </button>
      </div>
      <small>JPG, PNG or WebP · up to 5 MB each · private to your brief</small>
      {!d.references.length && (
        <div className="board-empty">
          <img
            src="/media/bespoke/design-reference-640.webp"
            alt="Ivory kurta design reference"
            width="220"
            height="220"
          />
          <p>
            Your ideas belong here.
            <br />
            <span>Start with a photo, or use our reference.</span>
          </p>
        </div>
      )}
      <div className="reference-grid">
        {d.references.map((r, i) => (
          <article key={r.asset_id}>
            <button
              className="pinned-image pin-target"
              aria-label={`Add detail to ${r.name}`}
              onClick={(e) => {
                if (r.pins.length >= 20) return;
                const rect = e.currentTarget.getBoundingClientRect();
                setPin({
                  index: i,
                  x: e.detail
                    ? ((e.clientX - rect.left) / rect.width) * 100
                    : 50,
                  y: e.detail
                    ? ((e.clientY - rect.top) / rect.height) * 100
                    : 50,
                });
                setNote("");
              }}
            >
              <img
                src={referenceSrc(r.asset_id)}
                alt={r.name}
                width="480"
                height="480"
              />
              {r.pins.map((p, n) => (
                <span
                  className="detail-pin"
                  key={n}
                  style={{ left: `${p.x}%`, top: `${p.y}%` }}
                >
                  {n + 1}
                </span>
              ))}
            </button>
            <div className="reference-caption">
              <b>
                {i + 1}. {r.name}
              </b>
              <button
                aria-label={`Remove reference ${i + 1}`}
                onClick={() =>
                  onChange({
                    ...d,
                    references: d.references.filter((_, n) => n !== i),
                  })
                }
              >
                Remove
              </button>
            </div>
            <ol>
              {r.pins.map((p, n) => (
                <li key={n}>
                  <b>{p.part}</b> — {p.note}
                  <button
                    aria-label={`Remove detail ${n + 1} from reference ${i + 1}`}
                    onClick={() =>
                      onChange({
                        ...d,
                        references: d.references.map((v, j) =>
                          j === i
                            ? { ...v, pins: v.pins.filter((_, k) => k !== n) }
                            : v,
                        ),
                      })
                    }
                  >
                    ×
                  </button>
                </li>
              ))}
            </ol>
            <button
              className="text-button"
              disabled={r.pins.length >= 20}
              onClick={() => {
                setPin({ index: i, x: 50, y: 50 });
                setNote("");
              }}
            >
              + Add detail
            </button>
          </article>
        ))}
      </div>
      <div className="voice-box">
        <div>
          <h3>Say it in your own words.</h3>
          <p>A voice note can help explain the feeling. Up to two minutes.</p>
        </div>
        <button
          className="button"
          disabled={busy || uploading}
          onClick={() => void record()}
        >
          {recording
            ? `STOP · ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`
            : "RECORD A VOICE NOTE"}
        </button>
        {recording && (
          <p role="status">
            Recording. Stay on this step until your note has uploaded.
          </p>
        )}
        {d.voice_id && (
          <>
            <audio controls src={referenceSrc(d.voice_id)} />
            <button
              className="text-button"
              onClick={() => onChange({ ...d, voice_id: "" })}
            >
              Remove voice note
            </button>
          </>
        )}
      </div>
      <Dialog
        open={referenceLibrary}
        onClose={() => setReferenceLibrary(false)}
        title="Studio reference library"
        className="reference-library-dialog"
      >
        <p className="studio-kicker">A STARTING POINT FOR YOUR IDEAS</p>
        <h2>The detail library.</h2>
        <p>
          Illustrative references. Add a photo and pin what you would like to
          keep or change.
        </p>
        <div className="studio-reference-library">
          {studioReferences.map((r) => (
            <button
              key={r.id}
              disabled={
                d.references.some((v) => v.asset_id === r.id) ||
                d.references.length >= 6
              }
              onClick={() => {
                onChange({
                  ...d,
                  references: [
                    ...d.references,
                    { asset_id: r.id, name: r.name, pins: [] },
                  ],
                });
                setReferenceLibrary(false);
              }}
            >
              <img src={asset(r.asset)} alt={r.name} width="640" height="640" />
              <span>{r.name}</span>
              <small>
                {d.references.some((v) => v.asset_id === r.id)
                  ? "ADDED"
                  : "ADD TO BOARD +"}
              </small>
            </button>
          ))}
        </div>
      </Dialog>
      <Dialog
        open={!!pin}
        onClose={() => setPin(null)}
        title="Add a design detail"
      >
        <h2>This bit, like this.</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!pin || !note.trim()) return;
            const p: Pin = { part, note: note.trim(), x: pin.x, y: pin.y };
            onChange({
              ...d,
              references: d.references.map((r, i) =>
                i === pin.index ? { ...r, pins: [...r.pins, p] } : r,
              ),
            });
            setPin(null);
          }}
        >
          <label className="field">
            Garment detail
            <select
              aria-label="Garment detail"
              value={part}
              onChange={(e) => setPart(e.target.value)}
            >
              {[
                "Neckline",
                "Sleeves",
                "Silhouette",
                "Hem and length",
                "Bottom",
                "Dupatta",
                "Lace placement",
                "Other",
              ].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <label className="field">
            What should masterji know?
            <textarea
              autoFocus
              required
              maxLength={1000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Use this sleeve shape, but make it full length."
            />
          </label>
          <button className="button primary">ADD DETAIL</button>
        </form>
      </Dialog>
    </div>
  );
}
