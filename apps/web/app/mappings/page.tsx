"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, Mapping } from "@/lib/api";

type HistoryItem = {
  id: string;
  action: string;
  snapshot: Record<string, unknown>;
  created_at: string;
};

function MappingRow({ mapping, refresh }: { mapping: Mapping; refresh: () => Promise<void> }) {
  const [sku, setSku] = useState(mapping.vendor_sku || "");
  const [description, setDescription] = useState(mapping.normalized_description);
  const [upc, setUpc] = useState(mapping.upc);
  const [units, setUnits] = useState(mapping.units_per_case?.toString() || "");
  const [history, setHistory] = useState<HistoryItem[] | null>(null);
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      await api<Mapping>(`/api/mappings/${mapping.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vendor_sku: sku || null,
          description,
          upc,
          units_per_case: units ? Number(units) : null,
        }),
      });
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!window.confirm("Soft-delete this product mapping? Historical invoices will keep their saved UPC snapshots.")) return;
    setBusy(true);
    try {
      await api<Mapping>(`/api/mappings/${mapping.id}`, { method: "DELETE" });
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function toggleHistory() {
    if (history) {
      setHistory(null);
      return;
    }
    setHistory(await api<HistoryItem[]>(`/api/mappings/${mapping.id}/history`));
  }

  return (
    <>
      <tr>
        <td>{mapping.vendor_name}</td>
        <td><input value={sku} onChange={e => setSku(e.target.value)} /></td>
        <td><input value={description} onChange={e => setDescription(e.target.value)} /></td>
        <td><input value={upc} onChange={e => setUpc(e.target.value)} /></td>
        <td><input value={units} onChange={e => setUnits(e.target.value)} /></td>
        <td>
          <div className="row">
            <button onClick={save} disabled={busy}>Save</button>
            <button className="secondary" onClick={toggleHistory} disabled={busy}>History</button>
            <button className="danger" onClick={remove} disabled={busy}>Delete</button>
          </div>
        </td>
      </tr>
      {history && (
        <tr>
          <td colSpan={6}>
            {history.length === 0 ? <span className="muted">No history.</span> : history.map(item => (
              <div className="issue" key={item.id}>
                <strong>{item.action}</strong> · {new Date(item.created_at).toLocaleString()} · UPC {String(item.snapshot.upc ?? "—")} · units/case {String(item.snapshot.units_per_case ?? "—")}
              </div>
            ))}
          </td>
        </tr>
      )}
    </>
  );
}

export default function MappingsPage() {
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ vendor_name: "", vendor_sku: "", description: "", upc: "", units_per_case: "" });

  async function load() {
    try {
      setMappings(await api<Mapping[]>("/api/mappings"));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load mappings");
    }
  }
  useEffect(() => { load(); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api<Mapping>("/api/mappings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vendor_name: form.vendor_name,
          vendor_sku: form.vendor_sku || null,
          description: form.description,
          upc: form.upc,
          units_per_case: form.units_per_case ? Number(form.units_per_case) : null,
        }),
      });
      setForm({ vendor_name: "", vendor_sku: "", description: "", upc: "", units_per_case: "" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  return (
    <div className="grid">
      <section>
        <h1>Product mappings</h1>
        <p>Confirmed vendor product → UPC and pack-size mappings. Edit, inspect history, or soft-delete mappings without rewriting historical invoices.</p>
      </section>
      <section className="card">
        <h2>Add or reactivate mapping</h2>
        <form onSubmit={create} className="form-grid">
          <label>Vendor<input required value={form.vendor_name} onChange={e => setForm({ ...form, vendor_name: e.target.value })} /></label>
          <label>Vendor SKU<input value={form.vendor_sku} onChange={e => setForm({ ...form, vendor_sku: e.target.value })} /></label>
          <label>Description<input required value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label>
          <label>UPC<input required value={form.upc} onChange={e => setForm({ ...form, upc: e.target.value })} /></label>
          <label>Units / case<input inputMode="numeric" value={form.units_per_case} onChange={e => setForm({ ...form, units_per_case: e.target.value })} /></label>
          <button>Save mapping</button>
        </form>
        {error && <div className="error">{error}</div>}
      </section>
      <section className="card">
        <h2>Active mappings</h2>
        {mappings.length === 0 ? <p>No mappings yet.</p> : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead><tr><th>Vendor</th><th>SKU</th><th>Description</th><th>UPC</th><th>Units/case</th><th>Actions</th></tr></thead>
              <tbody>{mappings.map(mapping => <MappingRow key={mapping.id} mapping={mapping} refresh={load} />)}</tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
