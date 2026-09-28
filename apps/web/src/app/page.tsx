"use client";

import { FormEvent, useEffect, useState } from "react";

type Vendor = { id: string; name: string };
type MappingHistory = {
  id: string;
  action: string;
  old_upc: string | null;
  new_upc: string | null;
  old_units_per_case: number | null;
  new_units_per_case: number | null;
  reason: string | null;
  changed_by: string;
  created_at: string;
};
type Mapping = {
  id: string;
  vendor_id: string;
  vendor_name: string;
  product_id: string;
  vendor_sku: string | null;
  vendor_description: string;
  units_per_case: number;
  upc: string;
  canonical_name: string;
  active: boolean;
};
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
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [vendorId, setVendorId] = useState("");
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [editingMappingId, setEditingMappingId] = useState<string | null>(null);
  const [historyMappingId, setHistoryMappingId] = useState<string | null>(null);
  const [mappingHistory, setMappingHistory] = useState<MappingHistory[]>([]);
  const [editingLineId, setEditingLineId] = useState<string | null>(null);
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

  async function reloadMappings() {
    const response = await fetch(`${API}/api/mappings?include_inactive=true`);
    if (response.ok) setMappings(await response.json());
  }

  useEffect(() => {
    void reloadVendors();
    void reloadMappings();
  }, []);

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
      setEditingLineId(null);
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
        units_per_case: Number(data.get("units_per_case")),
        reason: line.upc ? "Corrected during invoice review" : "Initial product mapping"
      })
    });
    if (!response.ok) return setError(await response.text());
    setInvoice(await response.json());
    setEditingLineId(null);
    await reloadMappings();
  }

  async function updateSavedMapping(mapping: Mapping, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch(`${API}/api/mappings/${mapping.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        upc: data.get("upc"),
        canonical_name: data.get("canonical_name"),
        units_per_case: Number(data.get("units_per_case")),
        reason: data.get("reason") || null
      })
    });
    if (!response.ok) return setError(await response.text());
    setEditingMappingId(null);
    await reloadMappings();
  }

  async function showMappingHistory(mapping: Mapping) {
    setError("");
    const response = await fetch(`${API}/api/mappings/${mapping.id}/history`);
    if (!response.ok) return setError(await response.text());
    setMappingHistory(await response.json());
    setHistoryMappingId(mapping.id);
  }

  async function deleteSavedMapping(mapping: Mapping) {
    const approved = window.confirm(
      `Delete the saved mapping for ${mapping.vendor_name} / ${mapping.vendor_description}?\n\n` +
      `UPC: ${mapping.upc}\nPack: ${mapping.units_per_case}\n\n` +
      "Future invoices will require this product to be mapped again. Historical invoices will not be changed."
    );
    if (!approved) return;

    setError("");
    const response = await fetch(`${API}/api/mappings/${mapping.id}?reason=${encodeURIComponent("Deleted by user")}`, {
      method: "DELETE"
    });
    if (!response.ok) return setError(await response.text());
    if (editingMappingId === mapping.id) setEditingMappingId(null);
    await reloadMappings();
  }

  function mappingForm(line: Line) {
    return (
      <form key={`${line.id}-mapping`} onSubmit={e => mapLine(line, e)} className="mapping-box">
        <div>
          <strong>{line.upc ? `Correct: ${line.description}` : `Map: ${line.description}`}</strong>
          <p className="muted small">
            Saving this also updates the vendor mapping used by future invoices.
          </p>
        </div>
        <input name="upc" defaultValue={line.upc ?? ""} placeholder="UPC / barcode" required />
        <input name="canonical_name" defaultValue={line.description} placeholder="Product name" required />
        <input
          name="units_per_case"
          type="number"
          min="1"
          defaultValue={line.units_per_case ?? ""}
          placeholder="Units/case"
          required
        />
        <div className="row">
          <button type="submit">{line.upc ? "Update mapping" : "Save mapping"}</button>
          {line.upc && <button type="button" className="secondary" onClick={() => setEditingLineId(null)}>Cancel</button>}
        </div>
      </form>
    );
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
              <thead><tr><th>Product</th><th>UPC</th><th>Cases / Pack</th><th>Total Qty</th><th>Product Discount</th><th>Total Amount</th><th>Review</th><th>Mapping</th></tr></thead>
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
                    <td>
                      {line.upc ? (
                        <button className="small-button secondary" onClick={() => setEditingLineId(line.id)}>Change UPC / pack</button>
                      ) : (
                        <span className="status review">Mapping required</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {invoice.lines.filter(line => !line.upc || editingLineId === line.id).map(mappingForm)}

          <div className="summary-row">
            <p className="muted">General invoice discount: ${invoice.invoice_level_discount ?? "0.00"} — stored for audit, ignored in product export.</p>
            {invoice.status === "ready" ? (
              <a className="button-link" href={`${API}/api/invoices/${invoice.id}/export.csv`}>Download CSV</a>
            ) : <span className="status review">Resolve review items to export</span>}
          </div>
        </section>
      )}

      <section className="card wide">
        <div className="row between">
          <div>
            <p className="eyebrow">SAVED PRODUCT MEMORY</p>
            <h2>Products & mappings</h2>
          </div>
          <span className="status">{mappings.filter(mapping => mapping.active).length} active</span>
        </div>
        <p className="muted small">
          Edit a UPC or pack size when a barcode was mapped incorrectly or the vendor changes a product UPC. Delete removes the mapping from future matching only; historical invoices keep their original UPC.
        </p>

        {mappings.length === 0 ? (
          <p className="muted">No product mappings saved yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Vendor</th><th>Vendor Product</th><th>Vendor SKU</th><th>UPC</th><th>Units / Case</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {mappings.map(mapping => (
                  <tr key={mapping.id} className={mapping.active ? "" : "inactive-row"}>
                    <td>{mapping.vendor_name}</td>
                    <td>{mapping.vendor_description}</td>
                    <td>{mapping.vendor_sku ?? "—"}</td>
                    <td><strong>{mapping.upc}</strong></td>
                    <td>{mapping.units_per_case}</td>
                    <td><span className={`status ${mapping.active ? "ready" : "review"}`}>{mapping.active ? "Active" : "Deleted"}</span></td>
                    <td>
                      <div className="row">
                        {mapping.active && <button className="small-button secondary" onClick={() => setEditingMappingId(mapping.id)}>Edit</button>}
                        <button className="small-button secondary" onClick={() => void showMappingHistory(mapping)}>History</button>
                        {mapping.active && <button className="small-button danger" onClick={() => void deleteSavedMapping(mapping)}>Delete</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {mappings.filter(mapping => editingMappingId === mapping.id).map(mapping => (
          <form key={`${mapping.id}-edit`} onSubmit={e => updateSavedMapping(mapping, e)} className="mapping-edit-box">
            <div>
              <strong>Edit {mapping.vendor_name} — {mapping.vendor_description}</strong>
              <p className="muted small">This change applies to future invoice matches. Existing invoice records are preserved.</p>
            </div>
            <label>UPC<input name="upc" defaultValue={mapping.upc} required /></label>
            <label>Product name<input name="canonical_name" defaultValue={mapping.canonical_name} required /></label>
            <label>Units / case<input name="units_per_case" type="number" min="1" defaultValue={mapping.units_per_case} required /></label>
            <label>Reason (optional)<input name="reason" placeholder="Wrong barcode / UPC changed" /></label>
            <div className="row">
              <button type="submit">Save changes</button>
              <button type="button" className="secondary" onClick={() => setEditingMappingId(null)}>Cancel</button>
            </div>
          </form>
        ))}

        {mappings.filter(mapping => historyMappingId === mapping.id).map(mapping => (
          <div key={`${mapping.id}-history`} className="history-box">
            <div className="row between">
              <div>
                <strong>Mapping history — {mapping.vendor_name} / {mapping.vendor_description}</strong>
                <p className="muted small">Create, edit, delete, and reactivation events are retained for audit.</p>
              </div>
              <button className="small-button secondary" onClick={() => setHistoryMappingId(null)}>Close</button>
            </div>
            {mappingHistory.length === 0 ? <p className="muted">No history yet.</p> : (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>When</th><th>Action</th><th>Old UPC</th><th>New UPC</th><th>Old Pack</th><th>New Pack</th><th>Reason</th></tr></thead>
                  <tbody>
                    {mappingHistory.map(entry => (
                      <tr key={entry.id}>
                        <td>{new Date(entry.created_at).toLocaleString()}</td>
                        <td>{entry.action}</td>
                        <td>{entry.old_upc ?? "—"}</td>
                        <td>{entry.new_upc ?? "—"}</td>
                        <td>{entry.old_units_per_case ?? "—"}</td>
                        <td>{entry.new_units_per_case ?? "—"}</td>
                        <td>{entry.reason ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </section>
    </main>
  );
}
