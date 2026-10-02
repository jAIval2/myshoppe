import { OrderDetail } from "@/features/account";
export const metadata = { title: "Your order", robots: { index: false } };
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <OrderDetail id={(await params).id} />;
}
