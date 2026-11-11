export type Material = {
  id: string;
  name: string;
  description: string;
  category: string;
};
export const fabrics: Material[] = [
  {
    id: "fabric-mocha",
    name: "Mocha garden",
    description: "Tonal botanical embroidery",
    category: "Embroidered",
  },
  {
    id: "fabric-pistachio",
    name: "Pistachio",
    description: "Soft colour, open weave",
    category: "Plain",
  },
  {
    id: "fabric-ivory",
    name: "Warm ivory",
    description: "Natural slub texture",
    category: "Plain",
  },
  {
    id: "fabric-rose",
    name: "Dusty rose",
    description: "Matte crepe texture",
    category: "Plain",
  },
  {
    id: "fabric-midnight",
    name: "Midnight blue",
    description: "A quiet satin sheen",
    category: "Plain",
  },
  {
    id: "fabric-clay",
    name: "Clay",
    description: "Earth-toned woven texture",
    category: "Plain",
  },
  {
    id: "fabric-sage",
    name: "Sage bloom",
    description: "Sheer floral embroidery",
    category: "Embroidered",
  },
  {
    id: "fabric-champagne",
    name: "Champagne",
    description: "Subtle floral jacquard",
    category: "Textured",
  },
  {
    id: "fabric-charcoal",
    name: "Charcoal",
    description: "Fine herringbone texture",
    category: "Textured",
  },
  {
    id: "fabric-marigold",
    name: "Marigold",
    description: "Soft crinkled texture",
    category: "Textured",
  },
];
export const laces: Material[] = [
  {
    id: "lace-scallop",
    name: "The scalloped edge",
    description: "Ivory curves · embroidered",
    category: "Lace",
  },
  {
    id: "lace-fine",
    name: "A fine line",
    description: "Antique gold · narrow loops",
    category: "Lace",
  },
  {
    id: "lace-floral",
    name: "Little flowers",
    description: "Ivory floral · open mesh",
    category: "Lace",
  },
  {
    id: "lace-geometric",
    name: "Quiet geometry",
    description: "Sand diamonds · woven border",
    category: "Lace",
  },
  {
    id: "lace-pearl",
    name: "Pearl finish",
    description: "Ivory · bead-edged trim",
    category: "Lace",
  },
  {
    id: "lace-leaf",
    name: "Leaf trail",
    description: "Sage · embroidered vine",
    category: "Lace",
  },
];
export const material = (id: string) =>
  [...fabrics, ...laces].find((x) => x.id === id);
export const asset = (id: string, width = 640) =>
  `/media/bespoke/${id}-${width}.webp`;
export const studioReferences = [
  { id: "sample", asset: "design-reference", name: "The complete silhouette" },
  {
    id: "reference-neckline",
    asset: "reference-neckline",
    name: "A considered neckline",
  },
  {
    id: "reference-sleeves",
    asset: "reference-sleeves",
    name: "The sleeve & cuff",
  },
  { id: "reference-hem", asset: "reference-hem", name: "The hem & side slit" },
  {
    id: "reference-dupatta",
    asset: "reference-dupatta",
    name: "A dupatta finish",
  },
];
export const referenceSrc = (id: string) => {
  const sample = studioReferences.find((r) => r.id === id);
  return sample ? asset(sample.asset, 1280) : `/api/bespoke-assets/${id}`;
};
export type Pin = { part: string; note: string; x: number; y: number };
export type Reference = { asset_id: string; name: string; pins: Pin[] };
export type Design = {
  name: string;
  occasion: string;
  requested_date: string | null;
  fabric: string;
  laces: string[];
  lace_choice: "" | "selected" | "none" | "help";
  quantity: string;
  placement: string;
  vision: string;
  silhouette: string;
  neckline: string;
  sleeves: string;
  length: string;
  bottom: string;
  dupatta: string;
  fit: string;
  units: "cm" | "in";
  measurements: string;
  fitting_plan: string;
  references: Reference[];
  voice_id: string;
};
export type Review = {
  instructions?: string;
  questions?: string;
  materials?: string;
  measurements?: string;
  owner?: string;
  reviewed_by?: string;
  at?: string;
};
export type Brief = {
  id: string;
  version: number;
  status: "draft" | "submitted" | "reviewing" | "agreed" | "ready";
  design: Design;
  review: Review;
  agreement: { version: number; at: string; name: string } | null;
  updated_at: string;
  history: {
    version: number;
    status: Brief["status"];
    event: string;
    at: string;
    design: Design;
    review: Review;
    agreement: Brief["agreement"];
  }[];
};
export const fresh = (): Design => ({
  name: "",
  occasion: "",
  requested_date: null,
  fabric: "",
  laces: [],
  lace_choice: "",
  quantity: "",
  placement: "",
  vision: "",
  silhouette: "",
  neckline: "",
  sleeves: "",
  length: "",
  bottom: "",
  dupatta: "",
  fit: "",
  units: "cm",
  measurements: "",
  fitting_plan: "",
  references: [],
  voice_id: "",
});
export const statusLabel = {
  draft: "Draft",
  submitted: "With the boutique",
  reviewing: "Review together",
  agreed: "Customer agreed",
  ready: "Ready for masterji",
};
export const designFields = [
  [
    "silhouette",
    "Silhouette",
    [
      "Straight kurta",
      "A-line kurta",
      "Anarkali",
      "Co-ord set",
      "Help me choose",
    ],
  ],
  [
    "neckline",
    "Neckline",
    ["Round", "V-neck", "Boat neck", "Mandarin collar", "As referenced"],
  ],
  [
    "sleeves",
    "Sleeves",
    ["Sleeveless", "Short", "Three-quarter", "Full length", "As referenced"],
  ],
  [
    "length",
    "Garment length",
    [
      "Hip length",
      "Knee length",
      "Calf length",
      "Ankle length",
      "Confirm at fitting",
    ],
  ],
  [
    "bottom",
    "Bottom",
    ["Straight trousers", "Palazzo", "Churidar", "No bottom", "As referenced"],
  ],
  [
    "dupatta",
    "Dupatta",
    ["Plain", "Lace edge", "Embroidered", "No dupatta", "As referenced"],
  ],
] as const;

// PostgreSQL JSONB may reorder object keys; that must not mark a saved brief dirty.
export function sameData(a: unknown, b: unknown): boolean {
  const normalize = (value: unknown): unknown =>
    Array.isArray(value)
      ? value.map(normalize)
      : value && typeof value === "object"
        ? Object.fromEntries(
            Object.entries(value)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([k, v]) => [k, normalize(v)]),
          )
        : value;
  return JSON.stringify(normalize(a)) === JSON.stringify(normalize(b));
}
