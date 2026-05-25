export type Priority = "low" | "medium" | "high";
export type QuantityUnit = "g" | "kg" | "ml" | "l" | "unit" | "pack" | "roll" | "bag" | "box";
export type StoreId = "plaza_vea" | "metro" | "vivanda" | "tottus";
export type Availability = "available" | "unavailable" | "unknown";

export interface ShoppingIntentItem {
  raw_text: string;
  product_query: string;
  quantity: number | null;
  unit: QuantityUnit | null;
  brand_preference: string | null;
  price_sensitivity: Priority;
  allow_substitution: boolean;
}

export interface ShoppingIntent {
  shopping_intent: ShoppingIntentItem[];
}

export interface ProductCandidate {
  store: StoreId;
  title: string;
  brand?: string | null;
  price: number;
  unit_price: number;
  quantity_value: number;
  quantity_unit: QuantityUnit;
  availability: Availability;
  product_url: string;
}

export interface CartItem {
  requested_item: string;
  selected_product: string;
  store: StoreId;
  unit_price: number;
  product_quantity_value: number;
  product_quantity_unit: QuantityUnit;
  required_units: number;
  effective_quantity: number;
  excess_quantity: number;
  estimated_total: number;
  product_url: string;
  reason: string;
  alternatives: ProductCandidate[];
}

export interface CartRecommendation {
  cart: CartItem[];
  total_estimated_cost: number;
  warnings: string[];
  questions: string[];
}

export interface UserPreferences {
  price_priority: Priority;
  brand_priority: Priority;
  known_brands_only: boolean;
  allow_substitutions: boolean;
  allow_equivalent_sizes: boolean;
  preferred_stores: StoreId[];
  excluded_brands: string[];
  preferred_brands: string[];
  max_candidates_per_product: number;
}

export interface CandidateDebug {
  title: string;
  store: StoreId;
  brand?: string | null;
  price: number;
  unit_price: number;
  filter_title: number;
  filter_brand: number;
  filter_category: number;
  filter_unit: number;
  filter_score: number;
  rank_relevance: number;
  rank_price: number;
  rank_unit: number;
  rank_brand: number;
  rank_store: number;
  rank_final: number;
}

export interface QueryDebug {
  query: string;
  scraped_total: number;
  scraped_per_store: Record<string, number>;
  passed_filter: number;
  candidates: CandidateDebug[];
}

export interface PipelineDebug {
  queries: QueryDebug[];
}

export interface ChatResponse {
  intent: ShoppingIntent | null;
  cart: CartRecommendation | null;
  candidate_products: Record<string, ProductCandidate[]>;
  warnings: string[];
  pipeline_debug: PipelineDebug | null;
}

export const STORE_LABELS: Record<StoreId, string> = {
  plaza_vea: "Plaza Vea",
  metro: "Metro",
  vivanda: "Vivanda",
  tottus: "Tottus",
};

export const STORE_COLORS: Record<StoreId, string> = {
  plaza_vea: "bg-orange-50 text-orange-600",
  metro:     "bg-sky-50 text-sky-700",
  vivanda:   "bg-pink-50 text-pink-600",
  tottus:    "bg-emerald-50 text-emerald-700",
};

export const PRIORITY_LABELS: Record<Priority, string> = {
  high: "Alta",
  medium: "Media",
  low: "Baja",
};
