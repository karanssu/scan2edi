"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, Invoice, InvoiceSummary } from "@/lib/api";

export default function HomePage() {
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      setInvoices(await api<InvoiceSummary[]>("/api/invoices"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load invoices");
    }
  }

  useEffect(() => { load(); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      const invoice = await api<Invoice>("/api/invoices", { method: "POST", body });
      window.location.href = `/invoices/${invoice.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid">
      <section>
        <h1>Invoice processing</h1>
        <p>Upload an invoice image or PDF. Google Document AI extracts the document; Scan2EDI applies deterministic vendor rules, saved UPC mappings, validation, and export logic.</p>
      </section>

      <section className="card">
        <h2>Process a new invoice</h2>
        <form className="upload" onSubmit={submit}>
          <div className="row space">
            <input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={e => setFile(e.target.files?.[0] || null)} />
            <button disabled={!file || busy}>{busy ? "Processing…" : "Upload & process"}</button>
          </div>
          {busy && <p>Sending the document to Document AI and applying Scan2EDI rules…</p>}
          {error && <div className="error">{error}</div>}
        </form>
      </section>

      <section className="card">
        <div className="row space"><h2>Recent invoices</h2><button className="secondary" onClick={load}>Refresh</button></div>
        {invoices.length === 0 ? <p>No invoices yet.</p> : (
          <table>
            <thead><tr><th>File</th><th>Vendor</th><th>Invoice</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {invoices.map(row => (
                <tr key={row.id}>
                  <td>{row.filename}</td>
                  <td>{row.vendor || "—"}</td>
                  <td>{row.invoice_number || "—"}</td>
                  <td><span className={`status ${row.status}`}>{row.status}</span></td>
                  <td><Link className="button secondary" href={`/invoices/${row.id}`}>Review</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
