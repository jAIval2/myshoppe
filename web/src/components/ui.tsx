"use client";
import { useEffect, useRef, type ReactNode } from "react";

export function Icon({
  name,
  size = 22,
}: {
  name: "plus" | "arrow" | "bookmark" | "close" | "chevron";
  size?: number;
}) {
  const paths = {
    plus: "M12 4v16M4 12h16",
    arrow: "M4 12h16m-7-7 7 7-7 7",
    bookmark: "M6 3h12v18l-6-4-6 4V3Z",
    close: "m5 5 14 14M19 5 5 19",
    chevron: "m6 9 6 6 6-6",
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}
export function Dialog({
  open,
  onClose,
  title,
  children,
  className = "",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
    if (open) {
      const old = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = old;
      };
    }
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-label={title}
      className={`dialog ${className}`}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose();
      }}
    >
      <div className="dialog-content">
        <button
          className="icon-button dialog-close"
          aria-label={`Close ${title}`}
          onClick={onClose}
        >
          <Icon name="close" />
        </button>
        {children}
      </div>
    </dialog>
  );
}
export function ErrorMessage({ error }: { error: unknown }) {
  return error ? (
    <p className="error" role="alert">
      {error instanceof Error ? error.message : String(error)}
    </p>
  ) : null;
}
export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="loading" role="status">
      <span className="loading-line" />
      {label}
    </div>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <h1>{title}</h1>
      {children}
    </div>
  );
}
