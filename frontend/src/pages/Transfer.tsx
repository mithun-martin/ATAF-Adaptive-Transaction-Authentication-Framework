import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  createTransaction,
  formatINR,
  getBeneficiaries,
  type Beneficiary,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Transfer() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [beneficiaryId, setBeneficiaryId] = useState("");
  const [amount, setAmount] = useState("");
  const [step, setStep] = useState<"form" | "confirm">("form");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    getBeneficiaries(token)
      .then(setBeneficiaries)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [token]);

  const selected = beneficiaries.find((b) => String(b.id) === beneficiaryId);

  function onContinue(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!selected) {
      setError("Please select a beneficiary");
      return;
    }
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("Enter a valid amount");
      return;
    }
    setStep("confirm");
  }

  async function onConfirm() {
    if (!token || !selected) return;
    setLoading(true);
    setError("");
    try {
      await createTransaction(token, selected.id, Number(amount));
      navigate("/transactions", { state: { message: "Transaction completed successfully." } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transfer failed");
      setStep("form");
    } finally {
      setLoading(false);
    }
  }

  if (beneficiaries.length === 0 && !error) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h1 className="text-2xl font-semibold mb-2">Transfer</h1>
        <p className="text-gray-600">
          You need to add a beneficiary first.{" "}
          <Link to="/beneficiaries" className="text-blue-700 hover:underline">
            Go to Beneficiaries
          </Link>
        </p>
      </div>
    );
  }

  if (step === "confirm" && selected) {
    return (
      <div className="max-w-lg bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <h1 className="text-2xl font-semibold">Confirm Transaction</h1>
        <div className="space-y-2 text-gray-800">
          <p>
            <span className="text-gray-500">To:</span> {selected.name}
          </p>
          <p>
            <span className="text-gray-500">Account:</span>{" "}
            {selected.masked_account || selected.account_number}
          </p>
          <p>
            <span className="text-gray-500">Amount:</span> {formatINR(Number(amount))}
          </p>
        </div>
        {error && <p className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</p>}
        <div className="flex gap-3">
          <button
            onClick={onConfirm}
            disabled={loading}
            className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded disabled:opacity-50"
          >
            {loading ? "Processing..." : "Confirm"}
          </button>
          <button
            onClick={() => setStep("form")}
            className="border border-gray-300 px-4 py-2 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Send Money</h1>
        <p className="text-sm text-gray-500 mt-1">Select a beneficiary and enter the amount.</p>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</p>}

      <form onSubmit={onContinue} className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
        <div>
          <label className="block text-sm mb-1">Select Beneficiary</label>
          <select
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={beneficiaryId}
            onChange={(e) => setBeneficiaryId(e.target.value)}
            required
          >
            <option value="">Choose...</option>
            {beneficiaries.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} — {b.masked_account || b.account_number} ({b.bank_name})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm mb-1">Amount (₹)</label>
          <input
            type="number"
            min="1"
            step="0.01"
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded">
          Continue
        </button>
      </form>
    </div>
  );
}
