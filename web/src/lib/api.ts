import type { components } from "./api-types";
export type Product = components["schemas"]["Product"];
export type Variant = components["schemas"]["Variant"];
export type ProductPage = components["schemas"]["ProductPage"];
export type ProductInput = components["schemas"]["ProductInput"];
export type Address = components["schemas"]["Address"];
export type Block = components["schemas"]["CampaignBlock"];
export type Department = "women" | "home";
export type Campaign = {
  id: string;
  department: Department;
  revision: number;
  published: boolean;
  content: { blocks: Block[] };
};
export type Session = {
  name: string | null;
  email: string | null;
  role: string | null;
  permissions: string[];
  development: boolean;
  payment_mode: string;
};
export type CartItem = {
  variant_id: string;
  product_id: string;
  title: string;
  slug: string;
  image: string;
  size: string;
  colour: string;
  quantity: number;
  price_paise: number;
  available: number;
  status: string;
};
export type Cart = {
  version: number;
  items: CartItem[];
  subtotal: number;
  count: number;
};
export type OrderItem = {
  id: string;
  quantity: number;
  shipped: number;
  returned: number;
  price_paise: number;
  snapshot: {
    title: string;
    image: string;
    colour: string;
    size: string;
    sku: string;
  };
};
export type Order = {
  id: string;
  number: number;
  total: number;
  subtotal: number;
  shipping: number;
  status: string;
  fulfilment: string;
  payment_mode: string;
  created_at: string;
  expires_at: string;
  address: Address;
  items: OrderItem[];
  refunds: { id: string; amount: number; status: string }[];
  returns: { id: string; status: string; reason: string }[];
  shipments: { id: string; tracking: string; status: string }[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public fields?: Record<string, string>,
    public requestId?: string,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: "same-origin",
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok)
    throw new ApiError(
      data.error?.message || "Request failed. Please try again.",
      data.error?.code,
      data.error?.fieldErrors,
      data.requestId,
    );
  return data;
}
export const json = (method: string, body?: unknown): RequestInit => ({
  method,
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
});
export const money = (paise: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(paise / 100);
export const titleCase = (value: string) =>
  value.replaceAll("-", " ").replace(/\b\w/g, (c) => c.toUpperCase());
export const categories: Record<Department, string[]> = {
  women: [
    "dresses",
    "tops",
    "trousers",
    "skirts",
    "knitwear",
    "outerwear",
    "co-ords",
  ],
  home: [
    "duvet-covers",
    "duvet-inserts",
    "bedsheets",
    "pillowcases",
    "quilts",
    "throws",
    "cushion-covers",
  ],
};
