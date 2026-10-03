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
  const [bankName, setBankName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
    setLoading(true);
    try {
      await addBeneficiary(token, name, accountNumber, bankName);
      setName("");
      setAccountNumber("");
      setBankName("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add beneficiary");
    } finally {
      setLoading(false);
    }
  }

  async function onDelete(id: number) {
    if (!token) return;
    if (!confirm("Delete this beneficiary?")) return;
    try {
      await deleteBeneficiary(token, id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Beneficiaries</h1>
        <p className="text-sm text-gray-500 mt-1">Add and manage people you can send money to.</p>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</p>}

      <form onSubmit={onAdd} className="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
        <h2 className="font-medium">Add Beneficiary</h2>
        <div className="grid md:grid-cols-3 gap-3">
          <input
            placeholder="Name"
            className="border border-gray-300 rounded px-3 py-2"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input
            placeholder="Account Number"
            className="border border-gray-300 rounded px-3 py-2"
            value={accountNumber}
            onChange={(e) => setAccountNumber(e.target.value)}
            required
          />
          <input
            placeholder="Bank Name"
            className="border border-gray-300 rounded px-3 py-2"
            value={bankName}
            onChange={(e) => setBankName(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {loading ? "Adding..." : "Add Beneficiary"}
        </button>
      </form>

      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="font-medium mb-3">Your Beneficiaries</h2>
        {list.length === 0 ? (
          <p className="text-sm text-gray-500">No beneficiaries yet.</p>
        ) : (
          <ul className="space-y-3">
            {list.map((b) => (
              <li
                key={b.id}
                className="flex items-center justify-between border border-gray-100 rounded p-3"
              >
                <div>
                  <p className="font-medium">{b.name}</p>
                  <p className="text-sm text-gray-600">
                    Account: {b.masked_account || b.account_number}
                  </p>
                  <p className="text-sm text-gray-600">Bank: {b.bank_name}</p>
                </div>
                <button
                  onClick={() => onDelete(b.id)}
                  className="text-sm text-red-600 hover:underline"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
