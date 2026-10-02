import { Help } from "@/features/help";
export default async function Page({
  params,
}: {
  params: Promise<{ slug?: string[] }>;
}) {
  return <Help slug={(await params).slug?.[0]} />;
}
