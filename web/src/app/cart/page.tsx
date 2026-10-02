import { Bag } from "@/features/cart";
export const metadata = { title: "Your bag", robots: { index: false } };
export default function Page() {
  return <Bag />;
}
