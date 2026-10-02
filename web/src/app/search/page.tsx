import { getProducts } from "@/lib/server";
import { Listing } from "@/features/listing";
export const metadata = { title: "Search", robots: { index: false } };
export default async function Search() {
  return (
    <main id="main">
      <Listing initial={await getProducts()} search />
    </main>
  );
}
