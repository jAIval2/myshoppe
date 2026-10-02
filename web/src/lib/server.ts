import type { ProductPage, Product, Campaign, Department } from "./api";
const origin = process.env.API_URL || "http://127.0.0.1:8000";
async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${origin}/api${path}`, { cache: "no-store" });
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
