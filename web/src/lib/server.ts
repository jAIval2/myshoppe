import type { ProductPage, Product, Campaign, Department } from "./api";
const origin = process.env.API_URL || "http://127.0.0.1:8000";
async function get<T>(path: string): Promise<T> {
  // Only this module is used for public catalogue/campaign DTOs. A short TTL
  // bounds freshness while keeping private actor and checkout state uncached.
  const response = await fetch(`${origin}/api${path}`, {
    cache: "force-cache",
    next: { revalidate: 60 },
  });
  if (!response.ok)
    throw new Error(`Catalogue unavailable (${response.status})`);
  return response.json();
}
export const getProducts = (params = "") =>
  get<ProductPage>(`/products?${params}`);
export const getProduct = (slug: string) =>
  get<Product>(`/products/${encodeURIComponent(slug)}`);
export const getCampaign = (department: Department) =>
  get<Campaign>(`/campaigns/${department}`);
