"use client";

import { FormEvent, useEffect, useState } from "react";

type Vendor = { id: string; name: string };
type Line = {
  id: string;
  line_number: number;
  description: string;
  upc: string | null;
  total_quantity: string | null;
  export_amount: string | null;
  needs_review: boolean;
  review_reason: string | null;
};
type Invoice = {
  id: string;
  invoice_number: string | null;
  status: string;
  invoice_level_discount: string | null;
  lines: Line[];
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [error, setError] = useState("");

  async function reloadVendors() {
    const response = await fetch(`${API}/api/vendors`);
    if (response.ok) setVendors(await response.json());
  }

  useEffect(() => { void reloadVendors(); }, []);

  async function addVendor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await fetch(`${API}/api/vendors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: data.get("name") })
    });
    if (!response.ok) return setError(await response.text());
    event.currentTarget.reset();
    await reloadVendors();
  }

  async function createDemoInvoice() {
    setError("");
    if (!vendors[0]) return setError("Create a vendor first.");
    const response = await fetch(`${API}/api/invoices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        vendor_id: vendors[0].id,
        invoice_number: "DEMO-001",
        invoice_level_discount: "10.00",
        lines: [
          {
            description: "Coke 20oz 24pk",
            case_quantity: "2",
            units_per_case: 24,
            case_price: "30.00",
            gross_amount: "60.00",
            product_discount: "5.00"
          }
        ]
      })
    });
    if (!response.ok) return setError(await response.text());
    setInvoice(await response.json());
  }

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">PRIVATE • ON-PREMISE</p>
          <h1>Scan2EDI</h1>
          <p>Scan invoices. Map products. Export total unit quantity and product net amount.</p>
        </div>
        <span className="status">Local-first</span>
      </header>

      <section className="grid">
        <article className="card">
          <h2>1. Vendor</h2>
          <form onSubmit={addVendor} className="row">
            <input name="name" placeholder="Coca-Cola" required />
            <button type="submit">Add vendor</button>
          </form>
          <div className="chips">
            {vendors.map(v => <span key={v.id}>{v.name}</span>)}
          </div>
        </article>

        <article className="card">
          <h2>2. Processing rule demo</h2>
          <p>2 cases × 24 = 48 units. $60 line − $5 product discount = $55. A general invoice discount is ignored.</p>
          <button onClick={createDemoInvoice}>Create demo invoice</button>
        </article>
      </section>

      {error && <p className="error">{error}</p>}

      {invoice && (
        <section className="card wide">
          <div className="row between">
            <div>
              <p className="eyebrow">INVOICE {invoice.invoice_number}</p>
              <h2>Review</h2>
            </div>
            <span className={`status ${invoice.status}`}>{invoice.status}</span>
          </div>
          <table>
            <thead><tr><th>Product</th><th>UPC</th><th>Total Quantity</th><th>Total Amount</th><th>Status</th></tr></thead>
            <tbody>
              {invoice.lines.map(line => (
                <tr key={line.id}>
                  <td>{line.description}</td>
                  <td>{line.upc ?? "Mapping required"}</td>
                  <td>{line.total_quantity ?? "—"}</td>
                  <td>{line.export_amount ? `$${line.export_amount}` : "—"}</td>
                  <td>{line.needs_review ? line.review_reason : "Ready"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">General invoice discount stored: ${invoice.invoice_level_discount ?? "0.00"} — intentionally not allocated to products.</p>
          <a className="button-link" href={`${API}/api/invoices/${invoice.id}/export.csv`}>Export CSV</a>
        </section>
      )}
    </main>
  );
}
