import { Favourites } from "@/features/cart";
export const metadata = { title: "Favourites", robots: { index: false } };
export default function Page() {
  return <Favourites />;
}
