import Link from "next/link";
export default function NotFound() {
  return (
    <main id="main" className="empty-state error-page">
      <h1>Something new awaits.</h1>
      <p>This page or product is no longer available.</p>
      <Link href="/" className="button">
        BACK TO MYSHOPPE
      </Link>
    </main>
  );
}
