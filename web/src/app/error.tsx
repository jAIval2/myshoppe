"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main id="main" className="empty-state error-page">
      <h1>A moment, please.</h1>
      <p>We couldn’t load the collection. Please try again.</p>
      <button className="button" onClick={reset}>
        TRY AGAIN
      </button>
    </main>
  );
}
