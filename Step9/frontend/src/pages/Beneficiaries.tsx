import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  addBeneficiary,
  deleteBeneficiary,
  getBeneficiaries,
  type Beneficiary,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Beneficiaries() {
  const { token } = useAuth();
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [bankName, setBankName] = useState("HDFC Bank");
  const [ifscCode, setIfscCode] = useState("HDFC0001234");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadBeneficiaries();
  }, [token]);

  function loadBeneficiaries() {
    if (!token) return;
    setLoading(true);
    getBeneficiaries(token)
      .then(setBeneficiaries)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load beneficiaries"))
      .finally(() => setLoading(false));
  }

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError("");
    setSaving(true);
    try {
      await addBeneficiary(token, {
        name,
        account_number: accountNumber,
        bank_name: bankName,
        ifsc_code: ifscCode,
      });
      setShowAddModal(false);
      setName("");
      setAccountNumber("");
      loadBeneficiaries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add beneficiary");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!token || !confirm("Are you sure you want to remove this beneficiary?")) return;
    try {
      await deleteBeneficiary(token, id);
      loadBeneficiaries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete beneficiary");
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Beneficiaries</h2>
          <p className="text-xs text-slate-400 mt-1">
            Manage recipients for adaptive transactions. Note: Brand new recipients elevate transaction risk score.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-all shadow-lg shadow-emerald-950"
        >
          + Add Beneficiary
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading beneficiaries...</div>
      ) : beneficiaries.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-400">
          No beneficiaries added yet. Add your first contact to begin testing transfers.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {beneficiaries.map((b) => (
            <div key={b.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative group hover:border-slate-700 transition-colors">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-lg font-bold text-white">{b.name}</h4>
                  <p className="text-xs text-slate-400 mt-0.5">{b.bank_name}</p>
                </div>
                <button
                  onClick={() => handleDelete(b.id)}
                  className="text-slate-500 hover:text-rose-400 text-xs p-1"
                  title="Remove"
                >
                  ✕
                </button>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-800 space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Account:</span>
                  <span className="text-slate-300 font-mono">{b.account_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">IFSC:</span>
                  <span className="text-slate-300 font-mono">{b.ifsc_code}</span>
                </div>
              </div>

              <div className="mt-6">
                <Link
                  to={`/transfer?ben=${b.id}`}
                  className="block text-center w-full bg-slate-800 hover:bg-emerald-600 hover:text-white text-emerald-400 text-xs font-semibold py-2 rounded-xl transition-all"
                >
                  Send Money
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4">Add New Beneficiary</h3>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Recipient Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Ramesh Patel"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Account Number</label>
                <input
                  type="text"
                  required
                  value={accountNumber}
                  onChange={(e) => setAccountNumber(e.target.value)}
                  placeholder="e.g. 50100234567890"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white font-mono text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Bank Name</label>
                  <input
                    type="text"
                    required
                    value={bankName}
                    onChange={(e) => setBankName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">IFSC Code</label>
                  <input
                    type="text"
                    required
                    value={ifscCode}
                    onChange={(e) => setIfscCode(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white font-mono text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-2 rounded-xl text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2 rounded-xl text-sm disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Beneficiary"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
