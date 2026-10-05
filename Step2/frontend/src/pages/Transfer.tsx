import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  cancelTransaction,
  formatINR,
  getAccount,
  getBeneficiaries,
  initiateTransaction,
  resendTransactionOTP,
  verifyTransactionOTP,
  type Account,
  type Beneficiary,
  type Transaction,
  type TransactionChallengeResponse,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

type FlowStep = "details" | "password" | "otp" | "success";

export default function Transfer() {
  const { token } = useAuth();
  const navigate = useNavigate();

  // Banking State
  const [account, setAccount] = useState<Account | null>(null);
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [beneficiaryId, setBeneficiaryId] = useState("");
  const [amount, setAmount] = useState("");
  const [remark, setRemark] = useState("");

  // Baseline 2FA State
  const [currentStep, setCurrentStep] = useState<FlowStep>("details");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [challenge, setChallenge] = useState<TransactionChallengeResponse | null>(null);
  const [completedTx, setCompletedTx] = useState<Transaction | null>(null);

  // UI State
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!token) return;
    Promise.all([getAccount(token), getBeneficiaries(token)])
      .then(([acc, bens]) => {
        setAccount(acc);
        setBeneficiaries(bens);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load account"));
  }, [token]);

  const selected = beneficiaries.find((b) => String(b.id) === beneficiaryId);

  // ── Step 1: Validate Details & Proceed to Password ──
  function onProceedToPassword(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!selected) {
      setError("Please select a beneficiary.");
      return;
    }
    const val = Number(amount);
    if (!val || val <= 0) {
      setError("Please enter a valid amount.");
      return;
    }
    if (account && val > account.balance) {
      setError(`Insufficient balance. Available: ${formatINR(account.balance)}`);
      return;
    }
    setCurrentStep("password");
  }

  // ── Step 2: Factor 1 (Password Verification) ──
  async function onSubmitPassword(e: FormEvent) {
    e.preventDefault();
    if (!token || !selected) return;
    if (!password) {
      setError("Account password is required for transaction authorization.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const challengeResp = await initiateTransaction(token, {
        beneficiary_id: selected.id,
        amount: Number(amount),
        remark: remark || undefined,
        password: password,
      });
      setChallenge(challengeResp);
      setPassword(""); // Clear password from state for security
      setCurrentStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password authentication failed");
    } finally {
      setLoading(false);
    }
  }

  // ── Step 3: Factor 2 (OTP Verification & Execution) ──
  async function onSubmitOTP(e: FormEvent) {
    e.preventDefault();
    if (!token || !challenge) return;
    if (otpCode.length !== 6) {
      setError("Please enter a valid 6-digit OTP.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const tx = await verifyTransactionOTP(token, challenge.challenge_id, otpCode);
      setCompletedTx(tx);
      // Refresh balance
      getAccount(token).then(setAccount).catch(() => {});
      setCurrentStep("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "OTP verification failed");
    } finally {
      setLoading(false);
    }
  }

  // Resend OTP
  async function onResendOTP() {
    if (!token || !challenge) return;
    setResending(true);
    setError("");
    try {
      const resp = await resendTransactionOTP(token, challenge.challenge_id);
      setChallenge(resp);
      setOtpCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend OTP");
    } finally {
      setResending(false);
    }
  }

  // Cancel Transaction
  async function onCancelChallenge() {
    if (token && challenge) {
      try {
        await cancelTransaction(token, challenge.challenge_id);
      } catch {
        /* ignore */
      }
    }
    setChallenge(null);
    setOtpCode("");
    setPassword("");
    setCurrentStep("details");
  }

  // No Beneficiaries Guard
  if (beneficiaries.length === 0 && !error) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 text-center max-w-lg mx-auto">
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

  return (
    <div className="max-w-xl mx-auto space-y-5">
      {/* System Banner */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold uppercase tracking-wider bg-indigo-700 text-white px-2 py-0.5 rounded">
            System 1: Baseline Authentication
          </span>
          <span className="text-xs text-indigo-700 font-semibold">Step 2 Implementation</span>
        </div>
        <p className="text-xs text-indigo-900">
          Enforces conventional 2FA: <strong>Password → OTP → Transaction</strong> before funds are finalized.
        </p>

        {/* Progress Pipeline */}
        <div className="mt-3 flex items-center justify-between text-xs text-indigo-800">
          <div className={`flex items-center gap-1 ${currentStep === "details" ? "font-bold text-indigo-950 underline" : ""}`}>
            <span className="w-5 h-5 rounded-full bg-indigo-200 flex items-center justify-center font-mono">1</span>
            Details
          </div>
          <span>→</span>
          <div className={`flex items-center gap-1 ${currentStep === "password" ? "font-bold text-indigo-950 underline" : ""}`}>
            <span className="w-5 h-5 rounded-full bg-indigo-200 flex items-center justify-center font-mono">2</span>
            Password
          </div>
          <span>→</span>
          <div className={`flex items-center gap-1 ${currentStep === "otp" ? "font-bold text-indigo-950 underline" : ""}`}>
            <span className="w-5 h-5 rounded-full bg-indigo-200 flex items-center justify-center font-mono">3</span>
            OTP
          </div>
          <span>→</span>
          <div className={`flex items-center gap-1 ${currentStep === "success" ? "font-bold text-green-700 underline" : ""}`}>
            <span className="w-5 h-5 rounded-full bg-green-200 flex items-center justify-center font-mono">✓</span>
            Executed
          </div>
        </div>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">{error}</p>}

      {/* ── STAGE 1: TRANSACTION DETAILS ── */}
      {currentStep === "details" && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Initiate Money Transfer</h1>
            <p className="text-sm text-gray-500 mt-1">
              Select recipient and amount.
              {account && <span className="ml-1">Available: <strong>{formatINR(account.balance)}</strong></span>}
            </p>
          </div>

          <form onSubmit={onProceedToPassword} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Select Beneficiary</label>
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
              <label className="block text-sm font-medium mb-1 text-gray-700">Amount (₹)</label>
              <input
                type="number"
                min="1"
                step="0.01"
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="Enter transfer amount"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Remark (optional)</label>
              <input
                type="text"
                maxLength={200}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
                value={remark}
                onChange={(e) => setRemark(e.target.value)}
                placeholder="e.g. Rent, Invoice, Grocery"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-blue-700 hover:bg-blue-800 text-white px-4 py-2.5 rounded-lg font-medium transition-colors"
            >
              Continue to Authentication (Factor 1) →
            </button>
          </form>
        </div>
      )}

      {/* ── STAGE 2: FACTOR 1 (PASSWORD VERIFICATION) ── */}
      {currentStep === "password" && selected && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-5">
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
              Factor 1 of 2: Password Authentication
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">Confirm Identity with Password</h2>
            <p className="text-sm text-gray-500">Please verify your account password to authorize transfer request.</p>
          </div>

          {/* Transfer Summary Preview */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 border border-gray-100">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Beneficiary:</span>
              <span className="font-semibold text-gray-800">{selected.name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Account:</span>
              <span className="font-mono text-gray-800">{selected.masked_account || selected.account_number}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Bank & IFSC:</span>
              <span className="text-gray-800">{selected.bank_name} ({selected.ifsc_code})</span>
            </div>
            {remark && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Remark:</span>
                <span className="text-gray-800">{remark}</span>
              </div>
            )}
            <hr className="border-gray-200 my-2" />
            <div className="flex justify-between text-base">
              <span className="font-medium text-gray-700">Amount:</span>
              <span className="font-bold text-blue-900 text-lg">{formatINR(Number(amount))}</span>
            </div>
          </div>

          <form onSubmit={onSubmitPassword} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Account Password</label>
              <input
                type="password"
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 outline-none"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your account password"
                autoFocus
                required
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading || !password}
                className="flex-1 bg-blue-700 hover:bg-blue-800 text-white px-4 py-2.5 rounded-lg font-medium disabled:opacity-50 transition-colors"
              >
                {loading ? "Verifying Password..." : "Verify Password & Request OTP →"}
              </button>
              <button
                type="button"
                onClick={() => setCurrentStep("details")}
                className="border border-gray-300 px-4 py-2.5 rounded-lg hover:bg-gray-50 font-medium transition-colors"
              >
                ← Edit Details
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── STAGE 3: FACTOR 2 (TRANSACTION OTP) ── */}
      {currentStep === "otp" && challenge && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-5">
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
              Factor 2 of 2: Transaction OTP
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">Enter Transaction OTP</h2>
            <p className="text-sm text-gray-500">
              {challenge.message}
            </p>
          </div>

          {/* Simulated OTP Banner */}
          {challenge.otp_display && (
            <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 text-center">
              <p className="text-xs text-amber-800 font-semibold mb-1">
                ⚠ SIMULATED TRANSACTION OTP (Simulating SMS for Research)
              </p>
              <p className="text-3xl font-mono font-bold tracking-widest text-amber-950">
                {challenge.otp_display}
              </p>
              <p className="text-xs text-amber-700 mt-1">
                Valid for authorizing {formatINR(challenge.amount)} to {challenge.beneficiary_name}
              </p>
            </div>
          )}

          <form onSubmit={onSubmitOTP} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-center text-gray-700">Enter 6-Digit OTP</label>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                className="w-full border border-gray-300 rounded-lg px-3 py-3 text-center text-3xl font-mono tracking-[0.5em] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="000000"
                autoFocus
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading || otpCode.length !== 6}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white py-3 rounded-lg font-medium disabled:opacity-50 transition-colors text-base"
            >
              {loading ? "Verifying OTP & Transferring..." : "✓ Verify OTP & Execute Transfer"}
            </button>
          </form>

          <div className="flex justify-between items-center text-sm pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onResendOTP}
              disabled={resending}
              className="text-blue-700 hover:underline disabled:opacity-50"
            >
              {resending ? "Sending new OTP..." : "Resend OTP"}
            </button>
            <button
              type="button"
              onClick={onCancelChallenge}
              className="text-red-600 hover:underline"
            >
              Cancel Transfer
            </button>
          </div>
        </div>
      )}

      {/* ── STAGE 4: SUCCESS RECEIPT ── */}
      {currentStep === "success" && completedTx && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm text-center space-y-4">
          <div className="w-16 h-16 bg-green-100 text-green-700 rounded-full flex items-center justify-center mx-auto text-3xl">
            ✓
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Transfer Completed!</h2>
          <p className="text-sm text-gray-500">
            Your transfer has been successfully processed under <strong>Baseline 2FA</strong>.
          </p>

          <div className="bg-gray-50 rounded-lg p-4 text-left space-y-2 border border-gray-100">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Reference ID:</span>
              <span className="font-mono font-semibold text-gray-800">{completedTx.reference_id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Transferred To:</span>
              <span className="font-semibold text-gray-800">{completedTx.beneficiary_name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Account:</span>
              <span className="font-mono text-gray-800">{completedTx.beneficiary_account}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Amount Sent:</span>
              <span className="font-bold text-blue-900">{formatINR(completedTx.amount)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Auth Mechanism:</span>
              <span className="text-xs bg-indigo-100 text-indigo-800 font-semibold px-2 py-0.5 rounded">
                Baseline (Password + OTP)
              </span>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => {
                setCompletedTx(null);
                setChallenge(null);
                setAmount("");
                setRemark("");
                setCurrentStep("details");
              }}
              className="flex-1 bg-blue-700 hover:bg-blue-800 text-white py-2.5 rounded-lg font-medium transition-colors"
            >
              Make Another Transfer
            </button>
            <button
              onClick={() => navigate("/transactions")}
              className="flex-1 border border-gray-300 py-2.5 rounded-lg hover:bg-gray-50 font-medium transition-colors"
            >
              View Transactions
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
