"use client";
import { useEffect, useState } from "react";
import {
  api,
  type Campaign,
  type Department,
  type ProductPage,
} from "@/lib/api";
import { CampaignJourney } from "@/features/campaign";
import { ErrorMessage, Loading } from "@/components/ui";

export default function CampaignPreview() {
  const [data, setData] = useState<{
    campaigns: Record<Department, Campaign>;
    products: Record<Department, ProductPage>;
    department: Department;
  } | null>(null);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const department: Department =
      params.get("department") === "home" ? "home" : "women";
    Promise.all([
      api<Campaign[]>(`/admin/campaigns/${department}`),
      api<Campaign>(`/campaigns/${department === "home" ? "women" : "home"}`),
      api<ProductPage>("/products?department=women"),
      api<ProductPage>("/products?department=home"),
    ])
      .then(([revisions, other, women, home]) => {
        const draft = revisions.find((r) => r.id === params.get("revision"));
        if (!draft)
          throw new Error(
            "Saved draft not found. Save your changes before previewing.",
          );
        setData({
          department,
          campaigns:
            department === "home"
              ? { home: draft, women: other }
              : { women: draft, home: other },
          products: { women, home },
        });
      })
      .catch(setError);
  }, []);
  if (error)
    return (
      <main id="main" className="standard-page">
        <ErrorMessage error={error} />
      </main>
    );
  if (!data) return <Loading />;
  return (
    <>
      <div className="draft-preview-label">SAVED DRAFT / NOT PUBLISHED</div>
      <CampaignJourney {...data} previewDepartment={data.department} />
    </>
  );
}
