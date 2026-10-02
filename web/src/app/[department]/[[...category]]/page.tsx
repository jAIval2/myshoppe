import { notFound } from "next/navigation";
import { getProducts } from "@/lib/server";
import { Listing } from "@/features/listing";
import { Footer } from "@/components/shell";
export default async function DepartmentPage({
  params,
}: {
  params: Promise<{ department: string; category?: string[] }>;
}) {
  const { department, category } = await params;
  if (department !== "women" && department !== "home") notFound();
  const initial = await getProducts(
    `department=${department}${category?.[0] ? `&category=${encodeURIComponent(category[0])}` : ""}`,
  );
  return (
    <>
      <main id="main">
        <Listing
          initial={initial}
          department={department}
          category={category?.[0]}
        />
      </main>
      <Footer />
    </>
  );
}
