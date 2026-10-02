import { AdminShell } from "@/features/admin";
export const metadata = {
  title: "Boutique administration",
  robots: { index: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
