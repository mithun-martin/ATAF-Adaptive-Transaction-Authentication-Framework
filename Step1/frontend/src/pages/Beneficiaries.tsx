import { FormEvent, useEffect, useState } from "react";
import {
  addBeneficiary,
  deleteBeneficiary,
  getBeneficiaries,
  type Beneficiary,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Beneficiaries() {
  const { token } = useAuth();
  const [list, setList] = useState<Beneficiary[]>([]);
  const [name, setName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [ifscCode, setIfscCode] = useState("OTHR0001234");
  const [bankName, setBankName] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  async function load() {
    if (!token) return;
    const data = await getBeneficiaries(token);
    setList(data);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [token]);

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      await addBeneficiary(token, {
        name,
        account_number: accountNumber,
        ifsc_code: ifscCode,
        bank_name: bankName,
        nickname: nickname || undefined,
      });
      setName("");
      setAccountNumber("");
      setIfscCode("OTHR0001234");
      setBankName("");
      setNickname("");
      setShowForm(false);
      setSuccess("Beneficiary added successfully.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add beneficiary");
    } finally {
      setLoading(false);
    }
  }

  async function onDelete(id: number, bName: string) {
    if (!token) return;
    if (!confirm(`Delete beneficiary "${bName}"?`)) return;
    setError("");
    try {
      await deleteBeneficiary(token, id);
      setSuccess("Beneficiary deleted.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Beneficiaries</h1>
          <p className="text-sm text-gray-500 mt-1">Manage people you can send money to</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          {showForm ? "Cancel" : "+ Add New"}
        </button>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}
      {success && <p className="text-sm text-green-700 bg-green-50 p-3 rounded-lg">{success}</p>}

      {/* Add Form */}
      {showForm && (
        <form onSubmit={onAdd} className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <h2 className="font-semibold text-lg">Add New Beneficiary</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Full Name *</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Recipient full name"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Nickname</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="Optional friendly name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Account Number *</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                placeholder="10-20 digit account number"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">IFSC Code</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={ifscCode}
                onChange={(e) => setIfscCode(e.target.value.toUpperCase())}
                placeholder="e.g. SBIN0001234"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Bank Name *</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                placeholder="e.g. State Bank of India"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-700 hover:bg-blue-800 text-white px-5 py-2.5 rounded-lg font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? "Adding..." : "Add Beneficiary"}
          </button>
        </form>
      )}

      {/* Beneficiary List */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {list.length === 0 ? (
          <p className="text-sm text-gray-500 p-6 text-center">No beneficiaries added yet.</p>
        ) : (
          <div className="divide-y divide-gray-100">
            {list.map((b) => (
              <div key={b.id} className="flex items-center justify-between p-4 hover:bg-gray-50">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900">
                    {b.name}
                    {b.nickname && <span className="text-gray-500 text-sm ml-2">({b.nickname})</span>}
                  </p>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500 mt-1">
                    <span>A/C: {b.masked_account || b.account_number}</span>
                    <span>IFSC: {b.ifsc_code}</span>
                    <span>Bank: {b.bank_name}</span>
                  </div>
                </div>
                <button
                  onClick={() => onDelete(b.id, b.name)}
                  className="text-sm text-red-600 hover:text-red-800 hover:underline ml-4 shrink-0"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
