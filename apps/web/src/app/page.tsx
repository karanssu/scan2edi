"use client";

import { FormEvent, useEffect, useState } from "react";

type Vendor = { id: string; name: string };
type Line = {
  id: string;
  line_number: number;
  description: string;
  upc: string | null;
  case_quantity: string | null;
  units_per_case: number | null;
  total_quantity: string | null;
  gross_amount: string | null;
  product_discount: string | null;
  export_amount: string | null;
  needs_review: boolean;
  review_reason: string | null;
};
type Invoice = {
  id: string;
  vendor_id: string;
  invoice_number: string | null;
  status: string;
  invoice_level_discount: string | null;
  lines: Line[];
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [vendorId, setVendorId] = useState("");
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function reloadVendors() {
    const response = await fetch(`${API}/api/vendors`);
    if (response.ok) {
      const data: Vendor[] = await response.json();
      setVendors(data);
      if (!vendorId && data[0]) setVendorId(data[0].id);
    }
  }

  useEffect(() => { void reloadVendors(); }, []);

  async function addVendor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    const response = await fetch(`${API}/api/vendors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: data.get("name") })
    });
    if (!response.ok) return setError(await response.text());
    const vendor: Vendor = await response.json();
    setVendorId(vendor.id);
    form.reset();
    await reloadVendors();
  }

  async function scanInvoice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const formData = new FormData(event.currentTarget);
      formData.set("vendor_id", vendorId);
      const response = await fetch(`${API}/api/invoices/scan`, { method: "POST", body: formData });
      if (!response.ok) throw new Error(await response.text());
      setInvoice(await response.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invoice processing failed");
    } finally {
      setBusy(false);
    }
  }

  async function mapLine(line: Line, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!invoice) return;
    setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch(`${API}/api/invoices/${invoice.id}/lines/${line.id}/map`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        upc: data.get("upc"),
        canonical_name: data.get("canonical_name") || line.description,
        units_per_case: Number(data.get("units_per_case"))
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
          <p>Invoice image → local AI extraction → saved UPC mapping → EDI-ready CSV.</p>
        </div>
        <span className="status">No cloud AI required</span>
      </header>

      <section className="grid">
        <article className="card">
          <h2>1. Vendors</h2>
          <form onSubmit={addVendor} className="row">
            <input name="name" placeholder="Coca-Cola" required />
            <button type="submit">Add</button>
          </form>
          <div className="chips">{vendors.map(v => <span key={v.id}>{v.name}</span>)}</div>
        </article>

        <article className="card">
          <h2>2. Scan invoice</h2>
          <form onSubmit={scanInvoice} className="stack">
            <select value={vendorId} onChange={e => setVendorId(e.target.value)} required>
              <option value="">Select vendor</option>
              {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
            </select>
            <input name="file" type="file" accept="image/png,image/jpeg,image/webp,application/pdf" required />
            <button type="submit" disabled={busy || !vendorId}>{busy ? "Processing locally…" : "Process invoice"}</button>
          </form>
          <p className="muted small">The invoice is stored and processed on your Scan2EDI server.</p>
        </article>
      </section>

      {error && <p className="error">{error}</p>}

      {invoice && (
        <section className="card wide">
          <div className="row between">
            <div>
              <p className="eyebrow">INVOICE {invoice.invoice_number ?? invoice.id.slice(0, 8)}</p>
              <h2>Review extracted products</h2>
            </div>
            <span className={`status ${invoice.status}`}>{invoice.status}</span>
          </div>

          <div className="table-wrap">
            <table>
              <thead><tr><th>Product</th><th>UPC</th><th>Cases / Pack</th><th>Total Qty</th><th>Product Discount</th><th>Total Amount</th><th>Review</th></tr></thead>
              <tbody>
                {invoice.lines.map(line => (
                  <tr key={line.id}>
                    <td>{line.description}</td>
                    <td>{line.upc ?? "—"}</td>
                    <td>{line.case_quantity ?? "—"} / {line.units_per_case ?? "—"}</td>
                    <td><strong>{line.total_quantity ?? "—"}</strong></td>
                    <td>{line.product_discount ? `$${line.product_discount}` : "—"}</td>
                    <td><strong>{line.export_amount ? `$${line.export_amount}` : "—"}</strong></td>
                    <td>{line.needs_review ? line.review_reason : "Ready"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {invoice.lines.filter(line => !line.upc).map(line => (
            <form key={line.id} onSubmit={e => mapLine(line, e)} className="mapping-box">
              <div>
                <strong>Map: {line.description}</strong>
                <p className="muted small">This mapping will be reused for future invoices from this vendor.</p>
              </div>
              <input name="upc" placeholder="UPC / barcode" required />
              <input name="canonical_name" defaultValue={line.description} placeholder="Product name" required />
              <input name="units_per_case" type="number" min="1" defaultValue={line.units_per_case ?? ""} placeholder="Units/case" required />
              <button type="submit">Save mapping</button>
            </form>
          ))}

          <div className="summary-row">
            <p className="muted">General invoice discount: ${invoice.invoice_level_discount ?? "0.00"} — stored for audit, ignored in product export.</p>
            {invoice.status === "ready" ? (
              <a className="button-link" href={`${API}/api/invoices/${invoice.id}/export.csv`}>Download CSV</a>
            ) : <span className="status review">Resolve review items to export</span>}
          </div>
        </section>
      )}
    </main>
  );
}
