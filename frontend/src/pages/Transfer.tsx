import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  createTransaction,
  formatINR,
  getAccount,
  getBeneficiaries,
  type Account,
  type Beneficiary,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Transfer() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [account, setAccount] = useState<Account | null>(null);
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [beneficiaryId, setBeneficiaryId] = useState("");
  const [amount, setAmount] = useState("");
  const [remark, setRemark] = useState("");
  const [step, setStep] = useState<"form" | "confirm">("form");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    Promise.all([getAccount(token), getBeneficiaries(token)])
      .then(([acc, bens]) => {
        setAccount(acc);
        setBeneficiaries(bens);
      })
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
    if (account && value > account.balance) {
      setError(`Insufficient balance. Available: ${formatINR(account.balance)}`);
      return;
    }
    setStep("confirm");
  }

  async function onConfirm() {
    if (!token || !selected) return;
    setLoading(true);
    setError("");
    try {
      await createTransaction(token, selected.id, Number(amount), remark || undefined);
      navigate("/transactions", { state: { message: "Transaction completed successfully!" } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transfer failed");
      setStep("form");
    } finally {
      setLoading(false);
    }
  }

  if (beneficiaries.length === 0 && !error) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 text-center">
        <h1 className="text-2xl font-bold mb-3">Send Money</h1>
        <p className="text-gray-600 mb-4">
          You need to add a beneficiary first before you can transfer money.
        </p>
        <Link
          to="/beneficiaries"
          className="bg-blue-700 hover:bg-blue-800 text-white px-5 py-2.5 rounded-lg font-medium inline-block"
        >
          Add Beneficiary
        </Link>
      </div>
    );
  }

  // Confirmation step
  if (step === "confirm" && selected && account) {
    return (
      <div className="max-w-lg mx-auto">
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
          <h1 className="text-2xl font-bold text-center">Confirm Transaction</h1>

          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">To</span>
              <span className="font-medium">{selected.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Account</span>
              <span className="font-mono text-sm">{selected.masked_account || selected.account_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">IFSC</span>
              <span className="font-mono text-sm">{selected.ifsc_code}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Bank</span>
              <span>{selected.bank_name}</span>
            </div>
            {remark && (
              <div className="flex justify-between">
                <span className="text-gray-500">Remark</span>
                <span className="text-sm">{remark}</span>
              </div>
            )}
            <hr className="border-gray-200" />
            <div className="flex justify-between text-lg">
              <span className="font-medium">Amount</span>
              <span className="font-bold text-blue-800">{formatINR(Number(amount))}</span>
            </div>
          </div>

          <div className="text-sm text-gray-500 text-center">
            Balance after transfer: {formatINR(account.balance - Number(amount))}
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}

          <div className="flex gap-3">
            <button
              onClick={onConfirm}
              disabled={loading}
              className="flex-1 bg-blue-700 hover:bg-blue-800 text-white px-4 py-2.5 rounded-lg font-medium disabled:opacity-50 transition-colors"
            >
              {loading ? "Processing..." : "✓ Confirm & Send"}
            </button>
            <button
              onClick={() => setStep("form")}
              className="flex-1 border border-gray-300 px-4 py-2.5 rounded-lg hover:bg-gray-50 font-medium transition-colors"
            >
              ← Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Form step
  return (
    <div className="max-w-lg mx-auto space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Send Money</h1>
        <p className="text-sm text-gray-500 mt-1">
          Select a beneficiary and enter the amount.
          {account && <span className="ml-1">Available: <strong>{formatINR(account.balance)}</strong></span>}
        </p>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}

      <form onSubmit={onContinue} className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Select Beneficiary</label>
          <select
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
            value={beneficiaryId}
            onChange={(e) => setBeneficiaryId(e.target.value)}
            required
          >
            <option value="">Choose beneficiary...</option>
            {beneficiaries.map((b) => (
              <option key={b.id} value={b.id}>
                {b.nickname || b.name} — {b.masked_account || b.account_number} ({b.bank_name})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Amount (₹)</label>
          <input
            type="number"
            min="1"
            step="0.01"
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Enter amount"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Remark (optional)</label>
          <input
            type="text"
            maxLength={200}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
            value={remark}
            onChange={(e) => setRemark(e.target.value)}
            placeholder="e.g. Rent payment, Gift, etc."
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-700 hover:bg-blue-800 text-white px-4 py-2.5 rounded-lg font-medium transition-colors"
        >
          Continue →
        </button>
      </form>
    </div>
  );
}
