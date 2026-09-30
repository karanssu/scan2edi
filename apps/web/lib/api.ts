export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type InvoiceSummary = {
  id: string;
  filename: string;
  vendor: string | null;
  invoice_number: string | null;
  status: string;
};

export type InvoiceLine = {
  id: string;
  sequence: number;
  confidence: number | null;
  vendor_sku: string | null;
  description: string;
  printed_upc: string | null;
  upc: string | null;
  case_quantity: string | null;
  units_per_case: number | null;
  direct_quantity: string | null;
  total_quantity: string | null;
  price: string | null;
  base_amount: string | null;
  deposit: string | null;
  discount: string | null;
  sugar_tax: string | null;
  line_total: string | null;
  export_total: string | null;
  needs_review: boolean;
  review_reasons: string[];
};

export type Invoice = {
  id: string;
  filename: string;
  vendor: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  status: string;
  reported_cases: string | null;
  reported_units: string | null;
  invoice_discount: string | null;
  invoice_tax: string | null;
  invoice_total: string | null;
  validation: {
    ready: boolean;
    issues: string[];
    warnings?: string[];
    calculated_cases?: string;
    calculated_units?: string;
    calculated_amount?: string;
    expected_invoice_total?: string | null;
  } | null;
  lines: InvoiceLine[];
};

export type Mapping = {
  id: string;
  vendor_name: string;
  vendor_sku: string | null;
  normalized_description: string;
  upc: string;
  units_per_case: number | null;
  active: boolean;
};

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail || JSON.stringify(body);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<T>;
}
