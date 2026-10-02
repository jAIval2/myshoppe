import { getProducts } from "@/lib/server";
import { Listing } from "@/features/listing";
import { Footer } from "@/components/shell";
import { notFound } from "next/navigation";
export default async function CollectionPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ entry?: string }>;
}) {
  const { slug } = await params;
  const department = slug.startsWith("home-")
    ? "home"
    : slug.startsWith("women-")
      ? "women"
      : null;
  if (!department) notFound();
  return (
    <>
      <main id="main">
        {(await searchParams).entry === "1" && (
          <section className="collection-entrance restored-entrance">
            <h1>THE NEW</h1>
            <a href="#collection-results">
              SCROLL DOWN
              <span className="vertical-line" />
            </a>
          </section>
        )}
        <div id="collection-results">
          <Listing
            department={department}
            initial={await getProducts(`department=${department}`)}
          />
        </div>
      </main>
      <Footer />
    </>
  );
}
