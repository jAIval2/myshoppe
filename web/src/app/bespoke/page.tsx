import { BespokeStudio } from "@/features/bespoke/studio";
import "@/features/bespoke/studio.css";
export const metadata = {
  title: "The Bespoke Studio | MyShoppe",
  description:
    "Choose a fabric, explore lace and create a personal design brief with MyShoppe.",
};
export default function Page() {
  return <BespokeStudio />;
}
