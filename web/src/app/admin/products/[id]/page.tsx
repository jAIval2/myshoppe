import { ProductEditor } from "@/features/admin";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <ProductEditor id={(await params).id} />;
}
