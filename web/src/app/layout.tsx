import type { Metadata } from "next";
import localFont from "next/font/local";
import { ShopProvider } from "@/components/shop-provider";
import { Shell } from "@/components/shell";
import "./globals.css";
const ui = localFont({
  src: "../../public/fonts/inter-0.woff2",
  variable: "--font-inter",
  weight: "400 900",
  display: "swap",
});
const editorial = localFont({
  src: "../../public/fonts/bodoni-0.woff2",
  variable: "--font-bodoni",
  weight: "400 500",
  display: "swap",
});
export const metadata: Metadata = {
  title: {
    default: "MyShoppe — Considered clothing. Thoughtful living.",
    template: "%s | MyShoppe",
  },
  description:
    "Discover a considered collection of women’s clothing and home textiles. A quieter perspective on everyday style.",
  metadataBase: new URL(process.env.PUBLIC_ORIGIN || "http://localhost:3000"),
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en-IN"
      data-scroll-behavior="smooth"
      className={`${ui.variable} ${editorial.variable}`}
    >
      <body>
        <ShopProvider>
          <Shell />
          {children}
        </ShopProvider>
      </body>
    </html>
  );
}
