"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE, api, Invoice, InvoiceLine } from "@/lib/api";

function LineEditor({ invoiceId, line, onSaved }: { invoiceId: string; line: InvoiceLine; onSaved: (i: Invoice) => void }) {
  const [upc, setUpc] = useState(line.upc || line.printed_upc || "");
  const [units, setUnits] = useState(line.units_per_case?.toString() || "");
  const [direct, setDirect] = useState(line.direct_quantity || "");
  const [cases, setCases] = useState(line.case_quantity || "");
  const [baseAmount, setBaseAmount] = useState(line.base_amount || "");
  const [deposit, setDeposit] = useState(line.deposit || "");
  const [discount, setDiscount] = useState(line.discount || "");
  const [lineTotal, setLineTotal] = useState(line.line_total || "");
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      const payload: Record<string, string | number | null> = {
        upc: upc || null,
        units_per_case: units ? Number(units) : null,
        direct_quantity: direct || null,
        case_quantity: cases || null,
        base_amount: baseAmount || null,
        deposit: deposit || null,
        discount: discount || null,
        line_total: lineTotal || null,
      };
      const updated = await api<Invoice>(`/api/invoices/${invoiceId}/lines/${line.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      onSaved(updated);
    } finally {
      setBusy(false);
    }
  }

  async function saveMapping() {
    if (!upc) return;
    setBusy(true);
    try {
      const updated = await api<Invoice>(`/api/invoices/${invoiceId}/lines/${line.id}/mapping`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          upc,
          units_per_case: units ? Number(units) : null,
        }),
      });
      onSaved(updated);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`line-card ${line.needs_review ? "review" : ""}`}>
      <div className="row space">
        <div><strong>#{line.sequence} {line.description}</strong><div className="muted">SKU: {line.vendor_sku || "—"} · Printed UPC: {line.printed_upc || "—"} · Confidence: {line.confidence == null ? "—" : `${Math.round(line.confidence * 100)}%`}</div></div>
        <div>{line.needs_review ? <span className="status review">review</span> : <span className="status ready">ready</span>}</div>
      </div>
      {line.review_reasons.map((reason, i) => <div key={i} className="issue">{reason}</div>)}
      <div className="form-grid" style={{ marginTop: 12 }}>
        <label>UPC<input value={upc} onChange={e => setUpc(e.target.value)} /></label>
        <label>Cases<input value={cases} onChange={e => setCases(e.target.value)} /></label>
        <label>Units / case<input value={units} onChange={e => setUnits(e.target.value)} /></label>
        <label>Direct qty<input value={direct} onChange={e => setDirect(e.target.value)} /></label>
        <label>Calculated qty<input disabled value={line.total_quantity || ""} /></label>
        <label>Base amount<input value={baseAmount} onChange={e => setBaseAmount(e.target.value)} /></label>
        <label>Deposit<input value={deposit} onChange={e => setDeposit(e.target.value)} /></label>
        <label>Discount<input value={discount} onChange={e => setDiscount(e.target.value)} /></label>
        <label>Printed line total<input value={lineTotal} onChange={e => setLineTotal(e.target.value)} /></label>
        <label>EDI amount<input disabled value={line.export_total || ""} /></label>
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <button onClick={save} disabled={busy}>{busy ? "Saving…" : "Save line"}</button>
        <button className="secondary" onClick={saveMapping} disabled={busy || !upc}>Confirm & save product mapping</button>
      </div>
    </div>
  );
}


function InvoiceHeaderEditor({ invoice, onSaved }: { invoice: Invoice; onSaved: (i: Invoice) => void }) {
  const [vendor, setVendor] = useState(invoice.vendor || "");
  const [number, setNumber] = useState(invoice.invoice_number || "");
  const [date, setDate] = useState(invoice.invoice_date || "");
  const [cases, setCases] = useState(invoice.reported_cases || "");
  const [units, setUnits] = useState(invoice.reported_units || "");
  const [invoiceDiscount, setInvoiceDiscount] = useState(invoice.invoice_discount || "");
  const [invoiceTax, setInvoiceTax] = useState(invoice.invoice_tax || "");
  const [total, setTotal] = useState(invoice.invoice_total || "");
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      const updated = await api<Invoice>(`/api/invoices/${invoice.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vendor: vendor || null,
          invoice_number: number || null,
          invoice_date: date || null,
          reported_cases: cases || null,
          reported_units: units || null,
          invoice_discount: invoiceDiscount || null,
          invoice_tax: invoiceTax || null,
          invoice_total: total || null,
        }),
      });
      onSaved(updated);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card">
      <h2>Invoice header</h2>
      <div className="form-grid">
        <label>Vendor<input value={vendor} onChange={e => setVendor(e.target.value)} /></label>
        <label>Invoice #<input value={number} onChange={e => setNumber(e.target.value)} /></label>
        <label>Date<input value={date} onChange={e => setDate(e.target.value)} /></label>
        <label>Reported cases<input value={cases} onChange={e => setCases(e.target.value)} /></label>
        <label>Reported units<input value={units} onChange={e => setUnits(e.target.value)} /></label>
        <label>General discount<input value={invoiceDiscount} onChange={e => setInvoiceDiscount(e.target.value)} /></label>
        <label>Tax<input value={invoiceTax} onChange={e => setInvoiceTax(e.target.value)} /></label>
        <label>Invoice total<input value={total} onChange={e => setTotal(e.target.value)} /></label>
      </div>
      <div className="row" style={{ marginTop: 12 }}><button onClick={save} disabled={busy}>{busy ? "Saving…" : "Save header"}</button></div>
    </section>
  );
}

export default function InvoicePage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Invoice>(`/api/invoices/${id}`).then(setInvoice).catch(err => setError(err.message));
  }, [id]);

  if (error) return <div className="card error">{error}</div>;
  if (!invoice) return <div className="card"><p>Loading…</p></div>;

  const validation = invoice.validation;
  return (
    <div className="grid">
      <section>
        <div className="row space">
          <div><h1>{invoice.vendor || "Unknown vendor"}</h1><p>{invoice.filename} · Invoice {invoice.invoice_number || "—"} · {invoice.invoice_date || "date unavailable"}</p></div>
          <span className={`status ${invoice.status}`}>{invoice.status}</span>
        </div>
      </section>

      <InvoiceHeaderEditor invoice={invoice} onSaved={setInvoice} />

      <section className="card">
        <div className="row space"><h2>Validation</h2>{validation?.ready && <a className="button" href={`${API_BASE}/api/invoices/${invoice.id}/export.csv`}>Download CSV</a>}</div>
        <div className="metrics">
          <div className="metric">Calculated cases<strong>{validation?.calculated_cases ?? "—"}</strong><span className="muted">Invoice: {invoice.reported_cases ?? "—"}</span></div>
          <div className="metric">Calculated units<strong>{validation?.calculated_units ?? "—"}</strong><span className="muted">Invoice: {invoice.reported_units ?? "—"}</span></div>
          <div className="metric">Calculated amount<strong>${validation?.calculated_amount ?? "—"}</strong><span className="muted">Invoice: {invoice.invoice_total ? `$${invoice.invoice_total}` : "—"}</span></div>
          <div className="metric">Products<strong>{invoice.lines.length}</strong><span className="muted">extracted lines</span></div>
        </div>
        {validation?.issues?.map((issue, i) => <div key={`issue-${i}`} className="issue">{issue}</div>)}
        {validation?.warnings?.map((warning, i) => <div key={`warning-${i}`} className="issue">Warning: {warning}</div>)}
        {validation?.ready && <p className="good">All required mappings and validation checks passed.</p>}
      </section>

      <section className="card"><h2>Product lines</h2>{invoice.lines.map(line => <LineEditor key={line.id} invoiceId={invoice.id} line={line} onSaved={setInvoice} />)}</section>
    </div>
  );
}
