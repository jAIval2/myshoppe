import { AdminOrder } from "@/features/admin";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <AdminOrder id={(await params).id} />;
}
