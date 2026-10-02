import { getCampaign, getProducts } from "@/lib/server";
import { CampaignJourney } from "@/features/campaign";
export default async function Home() {
  const [women, home, womenProducts, homeProducts] = await Promise.all([
    getCampaign("women"),
    getCampaign("home"),
    getProducts("department=women"),
    getProducts("department=home"),
  ]);
  return (
    <CampaignJourney
      campaigns={{ women, home }}
      products={{ women: womenProducts, home: homeProducts }}
    />
  );
}
