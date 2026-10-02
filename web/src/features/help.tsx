"use client";
import { useState } from "react";
import Link from "next/link";
import { api, json, titleCase } from "@/lib/api";
import { ErrorMessage } from "@/components/ui";
import { Footer } from "@/components/shell";
const pages: Record<string, { title: string; copy: string[] }> = {
  about: {
    title: "A quieter perspective.",
    copy: [
      "MyShoppe brings considered clothing and thoughtful home textiles together. Natural textures. Easy silhouettes. Pieces that find a place in the everyday.",
      "Our development collection explores the visual direction of the boutique. Product photography, manufacturing details and availability are being prepared for launch.",
    ],
  },
  delivery: {
    title: "Delivery & returns",
    copy: [
      "We are preparing domestic delivery across India. Your PIN code is checked and the delivery charge is shown before payment.",
      "This is a development storefront. Live delivery estimates, carrier details and the boutique’s return policy must be confirmed before orders open.",
      "For a development order, follow the order page in your account. Delivered orders can submit a return request there.",
    ],
  },
  privacy: {
    title: "Privacy",
    copy: [
      "Your bag, saved items and orders are stored against a private session. Your address is used to process your order. We do not store card or UPI credentials.",
      "Only essential session cookies are used in this preview. No advertising trackers are installed.",
      "The boutique’s legal identity, privacy contact and retention policy must be supplied before launch.",
    ],
  },
  terms: {
    title: "Terms of service",
    copy: [
      "The current storefront is a development preview. Development orders do not charge money and do not create a delivery commitment.",
      "Before launch, the boutique must publish its legal identity, verified product facts, pricing and tax terms, cancellation and return policies, and support contact.",
    ],
  },
  sizing: {
    title: "Finding your fit",
    copy: [
      "Choose a colour, then select a size. The exact price and availability are shown for the chosen variant.",
      "Garment measurements must be supplied by the boutique. Do not infer measurements from editorial photographs.",
    ],
  },
  bedding: {
    title: "A well-considered bed.",
    copy: [
      "Choose bedding by its actual dimensions, not just a Queen or King label. Measure your mattress and duvet before choosing a cover.",
      "A duvet cover and a duvet insert are different products. Check the contents of each pack; pillowcases and inserts are sold separately unless explicitly included.",
    ],
  },
};
export function Help({ slug = "help" }: { slug?: string }) {
  const [error, setError] = useState<unknown>(null);
  const [sent, setSent] = useState(false);
  const [pending, setPending] = useState(false);
  const page = pages[slug];
  async function contact(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError(null);
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await api(
        "/support",
        json("POST", { ...data, request_key: crypto.randomUUID() }),
      );
      setSent(true);
    } catch (e) {
      setError(e);
    } finally {
      setPending(false);
    }
  }
  return (
    <>
      <main id="main" className="help-page">
        <p className="eyebrow">MYSHOPPE / {slug.toUpperCase()}</p>
        <h1>
          {page?.title ||
            (slug === "contact" ? "Let’s talk." : "How can we help?")}
        </h1>
        {page ? (
          page.copy.map((p) => <p key={p}>{p}</p>)
        ) : slug === "contact" ? (
          <>
            <p>Send a request to the boutique’s support inbox.</p>
            <ErrorMessage error={error} />
            {sent ? (
              <p role="status">
                Your request is saved. You can continue exploring.
              </p>
            ) : (
              <form onSubmit={contact}>
                <label className="field">
                  Email
                  <input name="email" type="email" required />
                </label>
                <label className="field">
                  Subject
                  <input name="subject" minLength={3} required />
                </label>
                <label className="field">
                  Message
                  <textarea name="message" minLength={10} required />
                </label>
                <button className="button primary" disabled={pending}>
                  {pending ? "SENDING…" : "SEND REQUEST"}
                </button>
              </form>
            )}
          </>
        ) : (
          <div className="help-links">
            {[
              "delivery",
              "sizing",
              "bedding",
              "contact",
              "about",
              "privacy",
              "terms",
            ].map((key) => (
              <Link href={`/help/${key}`} key={key}>
                {titleCase(key)} <span>→</span>
              </Link>
            ))}
          </div>
        )}
      </main>
      <Footer />
    </>
  );
}
