"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { Campaign, Department, ProductPage, Block } from "@/lib/api";
import { Footer } from "@/components/shell";
import { Icon } from "@/components/ui";
import { Listing } from "./listing";

function CampaignVideo({ block }: { block: Block }) {
  const ref = useRef<HTMLVideoElement>(null);
  const [paused, setPaused] = useState(true);
  const [manual, setManual] = useState(false);
  useEffect(() => {
    const video = ref.current;
    if (!video) return;
    const reduced =
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
      Boolean(
        (navigator as Navigator & { connection?: { saveData?: boolean } })
          .connection?.saveData,
      );
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting && !manual && !reduced)
            video.play().catch(() => setPaused(true));
          else video.pause();
        }
      },
      { threshold: 0.4 },
    );
    observer.observe(video);
    const visibility = () => {
      if (document.hidden) video.pause();
    };
    document.addEventListener("visibilitychange", visibility);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", visibility);
      video.pause();
    };
  }, [manual]);
  return (
    <>
      <video
        ref={ref}
        src={block.src}
        poster={block.poster || undefined}
        muted
        loop
        playsInline
        preload="none"
        onPlay={() => setPaused(false)}
        onPause={() => setPaused(true)}
        aria-label="MyShoppe editorial campaign film"
      />
      <button
        className="video-control"
        onClick={() => {
          const v = ref.current;
          if (!v) return;
          if (v.paused) {
            setManual(false);
            v.play().catch(() => setPaused(true));
          } else {
            setManual(true);
            v.pause();
          }
        }}
      >
        {paused ? "PLAY FILM" : "PAUSE FILM"} <span>{paused ? "▷" : "Ⅱ"}</span>
      </button>
    </>
  );
}

export function CampaignJourney({
  campaigns,
  products,
  previewDepartment,
}: {
  campaigns: Record<Department, Campaign>;
  products: Record<Department, ProductPage>;
  previewDepartment?: Department;
}) {
  const [department, setDepartment] = useState<Department>(
    previewDepartment || "women",
  );
  const [active, setActive] = useState(0);
  const [pinned, setPinned] = useState(true);
  const [entered, setEntered] = useState(false);
  const [suppressed, setSuppressed] = useState(false);
  const track = useRef<HTMLDivElement>(null);
  const entrance = useRef<HTMLElement>(null);
  const start = useRef<{ x: number; y: number } | null>(null);
  const direction = useRef(0);
  const campaign = campaigns[department];
  const blocks = campaign.content.blocks.filter(
    (b) => b.type !== "collection-entry",
  );
  const target = `/collections/${department}-new-in`;
  useEffect(() => {
    if (previewDepartment) return;
    const value = new URLSearchParams(location.search).get("department");
    if (value === "home") setDepartment("home");
    const back = () => {
      setEntered(location.pathname.startsWith("/collections/"));
      setSuppressed(true);
    };
    addEventListener("popstate", back);
    return () => removeEventListener("popstate", back);
  }, []);
  useEffect(() => {
    if (
      !direction.current ||
      matchMedia("(prefers-reduced-motion: reduce)").matches
    )
      return;
    const hero = track.current?.querySelector(".hero .campaign-images");
    const animation = hero?.animate(
      [
        { transform: `translateX(${direction.current * 100}%)`, opacity: 0.65 },
        { transform: "translateX(0)", opacity: 1 },
      ],
      { duration: 560, easing: "cubic-bezier(.22,.68,0,1)", fill: "both" },
    );
    return () => animation?.cancel();
  }, [department]);
  useEffect(() => {
    const nodes = track.current?.querySelectorAll<HTMLElement>(
      "[data-campaign-block]",
    );
    if (!nodes) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries)
          if (entry.intersectionRatio >= 0.45)
            setActive(
              Number((entry.target as HTMLElement).dataset.campaignBlock),
            );
      },
      { threshold: [0.45, 0.65] },
    );
    nodes.forEach((n) => observer.observe(n));
    return () => observer.disconnect();
  }, [department]);
  useEffect(() => {
    let frame = 0,
      previous = scrollY,
      timer: ReturnType<typeof setTimeout> | undefined;
    const scroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const box = entrance.current?.getBoundingClientRect();
        if (!box) return;
        setPinned(box.top > innerHeight * 0.45);
        if (box.top > innerHeight && suppressed) setSuppressed(false);
        if (
          scrollY > previous &&
          box.top < innerHeight * 0.5 &&
          box.bottom > innerHeight * 0.4 &&
          !entered &&
          !suppressed &&
          !timer &&
          !previewDepartment
        ) {
          timer = setTimeout(() => {
            history.pushState({ campaignEntry: true }, "", `${target}?entry=1`);
            setEntered(true);
            timer = undefined;
          }, 200);
        }
        if (box.top >= innerHeight * 0.5 && timer) {
          clearTimeout(timer);
          timer = undefined;
        }
        previous = scrollY;
      });
    };
    addEventListener("scroll", scroll, { passive: true });
    scroll();
    return () => {
      removeEventListener("scroll", scroll);
      cancelAnimationFrame(frame);
      if (timer) clearTimeout(timer);
    };
  }, [entered, suppressed, target]);
  const change = (d: Department) => {
    if (d === department) return;
    direction.current = d === "home" ? 1 : -1;
    setDepartment(d);
    setActive(0);
    setEntered(false);
    setSuppressed(false);
    if (!previewDepartment)
      history.replaceState({}, "", d === "women" ? "/" : "/?department=home");
    window.scrollTo({ top: 0, behavior: "instant" });
  };
  function enter(e: React.MouseEvent<HTMLAnchorElement>) {
    e.preventDefault();
    if (!entered && !previewDepartment) {
      history.pushState({ campaignEntry: true }, "", `${target}?entry=1`);
      setEntered(true);
    }
    document.querySelector("#new-collection")?.scrollIntoView({
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
  }
  return (
    <main id="main" className="campaign-page">
      <div
        ref={track}
        className="campaign-track"
        data-testid="campaign-sequence"
        data-department={department}
      >
        {blocks.map((block, index) => (
          <section
            key={`${department}-${index}`}
            data-campaign-block={index}
            data-testid={
              block.type === "poster" ? "campaign-poster" : undefined
            }
            className={`campaign-block ${block.type} treatment-${block.layout} tone-${block.tone}`}
            onTouchStart={
              index === 0
                ? (e) => {
                    start.current = {
                      x: e.touches[0].clientX,
                      y: e.touches[0].clientY,
                    };
                  }
                : undefined
            }
            onTouchEnd={
              index === 0
                ? (e) => {
                    if (!start.current) return;
                    const dx = e.changedTouches[0].clientX - start.current.x,
                      dy = e.changedTouches[0].clientY - start.current.y;
                    if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.5)
                      change(department === "women" ? "home" : "women");
                    start.current = null;
                  }
                : undefined
            }
          >
            {block.type === "video" ? (
              <CampaignVideo block={block} />
            ) : (
              <div className="campaign-images">
                <img
                  src={block.src}
                  alt={
                    index === 0
                      ? `MyShoppe ${department} October editorial`
                      : block.subtitle || "MyShoppe editorial"
                  }
                  fetchPriority={index === 0 ? "high" : "auto"}
                  loading={index === 0 ? "eager" : "lazy"}
                />
                {block.layout === "split" && (
                  <img
                    src={block.mobile_src || block.src}
                    alt="A second perspective on the collection"
                    loading="lazy"
                  />
                )}
              </div>
            )}
            <div className="campaign-copy">
              {index === 0 ? <h1>{block.title}</h1> : <h2>{block.title}</h2>}
              <p>{block.subtitle}</p>
            </div>
            {index === 0 && (
              <div className="department-switch" aria-label="Choose department">
                <span>01 / 02</span>
                <div>
                  {(["women", "home"] as Department[]).map((d) => (
                    <button
                      key={d}
                      aria-label={`${d === "women" ? "Women" : "Home"} department`}
                      aria-pressed={department === d}
                      onClick={() => change(d)}
                    >
                      {d.toUpperCase()}
                    </button>
                  ))}
                </div>
                <button
                  className="icon-button"
                  aria-label={`Switch to ${department === "women" ? "Home" : "Women"}`}
                  onClick={() =>
                    change(department === "women" ? "home" : "women")
                  }
                >
                  <Icon name="arrow" />
                </button>
              </div>
            )}
          </section>
        ))}
      </div>
      <div
        className={`campaign-overlay ${pinned ? "visible" : ""} tone-${blocks[active]?.tone || "dark"}`}
        aria-hidden={!pinned}
      >
        <span className="campaign-wordmark" aria-hidden="true">
          myshoppe
        </span>
        <a
          href={target}
          aria-label={`Explore the ${department} new collection`}
          tabIndex={pinned ? 0 : -1}
          className="campaign-arrow"
          onClick={enter}
        >
          <Icon name="arrow" size={32} />
        </a>
      </div>
      <section ref={entrance} className="collection-entrance">
        <h2>THE NEW</h2>
        <a href={target} onClick={enter}>
          SCROLL DOWN
          <span className="vertical-line" />
        </a>
      </section>
      <section id="new-collection" className="new-collection">
        <Listing
          initial={products[department]}
          department={department}
          embedded
          key={department}
        />
      </section>
      <Footer />
    </main>
  );
}
