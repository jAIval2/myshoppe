import { getProduct, getProducts } from "@/lib/server";
import { ProductDetail } from "@/features/product";
import { notFound } from "next/navigation";
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  try {
    const p = await getProduct((await params).slug);
    return { title: p.title, description: p.description };
  } catch {
    return { title: "Product unavailable" };
  }
}
export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  let product;
  try {
    product = await getProduct((await params).slug);
  } catch {
    notFound();
  }
  const related = await getProducts(
    `department=${product.department}&limit=16`,
  );
  const curated = await Promise.allSettled(
    [...new Set(Object.values(product.relations || {}).flat())]
      .slice(0, 24)
      .map(getProduct),
  );
  const candidates = [
    ...curated.flatMap((r) =>
      r.status === "fulfilled" && r.value.department === product.department
        ? [r.value]
        : [],
    ),
    ...related.items,
  ];
  return (
    <ProductDetail
      product={product}
      related={[
        ...new Map(
          candidates.filter((p) => p.id !== product.id).map((p) => [p.id, p]),
        ).values(),
      ]}
    />
  );
}
