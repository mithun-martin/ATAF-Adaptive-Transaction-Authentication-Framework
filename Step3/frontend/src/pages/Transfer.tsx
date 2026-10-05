import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  cancelTransaction,
  confirmAdditionalVerification,
  formatINR,
  getAccount,
  getBeneficiaries,
  initiateTransaction,
  resendTransactionOTP,
  verifyTransactionOTP,
  type Account,
  type Beneficiary,
  type Transaction,
  type TransactionAdditionalVerificationStageResponse,
  type TransactionChallengeResponse,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

type FlowStep = "details" | "password" | "otp" | "additional_confirmation" | "success";

export default function Transfer() {
  const { token } = useAuth();
  const navigate = useNavigate();

  // Banking State
  const [account, setAccount] = useState<Account | null>(null);
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [beneficiaryId, setBeneficiaryId] = useState("");
  const [amount, setAmount] = useState("");
  const [remark, setRemark] = useState("");

  // Static 3FA Pipeline State
  const [currentStep, setCurrentStep] = useState<FlowStep>("details");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [challenge, setChallenge] = useState<TransactionChallengeResponse | null>(null);
  const [additionalStage, setAdditionalStage] =
    useState<TransactionAdditionalVerificationStageResponse | null>(null);

  // Factor 3 State
  const [transactionPin, setTransactionPin] = useState("");
  const [explicitConfirmed, setExplicitConfirmed] = useState(false);
  const [antiCoercionConfirmed, setAntiCoercionConfirmed] = useState(false);

  // Completed Tx State
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

  // ── Step 1: Validate Details ──
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
      setError("Account password is required for Factor 1 verification.");
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
      setPassword(""); // Clear password for security
      setCurrentStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password authentication failed");
    } finally {
      setLoading(false);
    }
  }

  // ── Step 3: Factor 2 (OTP Verification) ──
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
      // In Static 3FA, verifying OTP advances to Factor 3 (Additional Confirmation)
      const stageResp = await verifyTransactionOTP(token, challenge.challenge_id, otpCode);
      setAdditionalStage(stageResp);
      setCurrentStep("additional_confirmation");
    } catch (err) {
      setError(err instanceof Error ? err.message : "OTP verification failed");
    } finally {
      setLoading(false);
    }
  }

  // ── Step 4: Factor 3 (Transaction-Bound Additional Confirmation) ──
  async function onSubmitAdditionalConfirmation(e: FormEvent) {
    e.preventDefault();
    if (!token || !additionalStage) return;

    if (!explicitConfirmed) {
      setError("Please check the confirmation box acknowledging personal initiation.");
      return;
    }
    if (!antiCoercionConfirmed) {
      setError("Please confirm that you are not under coercion from a phone caller or unknown third party.");
      return;
    }
    if (!transactionPin || transactionPin.length < 4) {
      setError("Please enter your 4-digit Transaction Security PIN (Default PIN: 1234).");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const tx = await confirmAdditionalVerification(token, {
        challenge_id: additionalStage.challenge_id,
        transaction_pin: transactionPin,
        explicit_confirmation: true,
        anti_coercion_confirmation: true,
      });
      setCompletedTx(tx);
      // Refresh balance
      getAccount(token).then(setAccount).catch(() => {});
      setCurrentStep("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Additional verification failed");
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
  async function onCancelFlow() {
    const activeId = challenge?.challenge_id || additionalStage?.challenge_id;
    if (token && activeId) {
      try {
        await cancelTransaction(token, activeId);
      } catch {
        /* ignore */
      }
    }
    setChallenge(null);
    setAdditionalStage(null);
    setOtpCode("");
    setPassword("");
    setTransactionPin("");
    setExplicitConfirmed(false);
    setAntiCoercionConfirmed(false);
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
      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold uppercase tracking-wider bg-purple-700 text-white px-2.5 py-0.5 rounded">
            System 2: Static 3FA
          </span>
          <span className="text-xs text-purple-700 font-semibold">Step 3 Implementation</span>
        </div>
        <p className="text-xs text-purple-900">
          Enforces static 3-factor authentication:{" "}
          <strong>Password → OTP → Additional Confirmation → Transaction</strong> on <em>every single transaction</em>.
        </p>

        {/* 4-Step Visual Progress Bar */}
        <div className="mt-3 grid grid-cols-4 gap-1 text-center text-xs">
          <div
            className={`p-1.5 rounded ${
              currentStep === "details"
                ? "bg-purple-700 text-white font-bold"
                : "bg-purple-200/70 text-purple-900"
            }`}
          >
            1. Details
          </div>
          <div
            className={`p-1.5 rounded ${
              currentStep === "password"
                ? "bg-purple-700 text-white font-bold"
                : "bg-purple-200/70 text-purple-900"
            }`}
          >
            2. Password
          </div>
          <div
            className={`p-1.5 rounded ${
              currentStep === "otp"
                ? "bg-purple-700 text-white font-bold"
                : "bg-purple-200/70 text-purple-900"
            }`}
          >
            3. OTP
          </div>
          <div
            className={`p-1.5 rounded ${
              currentStep === "additional_confirmation"
                ? "bg-purple-700 text-white font-bold animate-pulse"
                : currentStep === "success"
                ? "bg-green-700 text-white font-bold"
                : "bg-purple-200/70 text-purple-900"
            }`}
          >
            4. Verify & Sign
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
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none"
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
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none"
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
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none"
                value={remark}
                onChange={(e) => setRemark(e.target.value)}
                placeholder="e.g. Rent, Vendor Payment, Consulting"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-purple-700 hover:bg-purple-800 text-white px-4 py-2.5 rounded-lg font-medium transition-colors"
            >
              Continue to Factor 1 (Password) →
            </button>
          </form>
        </div>
      )}

      {/* ── STAGE 2: FACTOR 1 (PASSWORD VERIFICATION) ── */}
      {currentStep === "password" && selected && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-5">
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
              Factor 1 of 3: Password Authentication
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">Confirm Account Password</h2>
            <p className="text-sm text-gray-500">Enter password to authorize the first factor of 3FA.</p>
          </div>

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
            <hr className="border-gray-200 my-2" />
            <div className="flex justify-between text-base">
              <span className="font-medium text-gray-700">Amount:</span>
              <span className="font-bold text-purple-900 text-lg">{formatINR(Number(amount))}</span>
            </div>
          </div>

          <form onSubmit={onSubmitPassword} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">Account Password</label>
              <input
                type="password"
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter account password"
                autoFocus
                required
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading || !password}
                className="flex-1 bg-purple-700 hover:bg-purple-800 text-white px-4 py-2.5 rounded-lg font-medium disabled:opacity-50 transition-colors"
              >
                {loading ? "Verifying..." : "Verify Factor 1 & Request OTP →"}
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

      {/* ── STAGE 3: FACTOR 2 (OTP VERIFICATION) ── */}
      {currentStep === "otp" && challenge && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-5">
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
              Factor 2 of 3: Out-of-band OTP
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">Enter Transaction OTP</h2>
            <p className="text-sm text-gray-500">{challenge.message}</p>
          </div>

          {/* Simulated OTP Banner */}
          {challenge.otp_display && (
            <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 text-center">
              <p className="text-xs text-amber-800 font-semibold mb-1">
                ⚠ SIMULATED TRANSACTION OTP (Simulating Out-of-Band SMS)
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
                className="w-full border border-gray-300 rounded-lg px-3 py-3 text-center text-3xl font-mono tracking-[0.5em] focus:ring-2 focus:ring-purple-500 outline-none"
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
              className="w-full bg-purple-700 hover:bg-purple-800 text-white py-3 rounded-lg font-medium disabled:opacity-50 transition-colors text-base"
            >
              {loading ? "Verifying OTP..." : "Verify Factor 2 & Proceed to Factor 3 →"}
            </button>
          </form>

          <div className="flex justify-between items-center text-sm pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onResendOTP}
              disabled={resending}
              className="text-purple-700 hover:underline disabled:opacity-50"
            >
              {resending ? "Sending new OTP..." : "Resend OTP"}
            </button>
            <button
              type="button"
              onClick={onCancelFlow}
              className="text-red-600 hover:underline"
            >
              Cancel Transfer
            </button>
          </div>
        </div>
      )}

      {/* ── STAGE 4: FACTOR 3 (TRANSACTION-BOUND ADDITIONAL CONFIRMATION) ── */}
      {currentStep === "additional_confirmation" && additionalStage && (
        <div className="bg-white border-2 border-amber-400 rounded-xl p-6 shadow-md space-y-5">
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider bg-amber-500 text-white px-3 py-1 rounded-full shadow-sm">
              Factor 3 of 3: Additional Confirmation (Static 3FA)
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-3 flex items-center justify-center gap-2">
              <span>⚠️</span>
              <span>Explicit Transaction-Bound Confirmation</span>
            </h2>
            <p className="text-xs text-amber-900 font-medium mt-1">
              Required for <strong>100% of transactions</strong> in Static 3FA regardless of amount or risk.
            </p>
          </div>

          {/* Prominent High-Risk / Static 3FA Callout box matching PDF Page 7 */}
          <div className="bg-amber-50 border border-amber-300 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-amber-200 pb-2">
              <span className="text-xs font-bold text-amber-800 uppercase tracking-wide">
                Security Authorization Target
              </span>
              <span className="text-xs font-mono bg-white px-2 py-0.5 rounded border border-amber-200 text-amber-900">
                Nonce: {additionalStage.nonce.slice(0, 8)}...
              </span>
            </div>

            <div className="text-center py-2">
              <div className="text-3xl font-extrabold text-amber-950 font-mono">
                {formatINR(additionalStage.amount)}
              </div>
              <div className="text-sm font-semibold text-gray-800 mt-1">
                → Account: {additionalStage.beneficiary_account} ({additionalStage.beneficiary_name})
              </div>
              <div className="text-xs text-gray-500">
                {additionalStage.bank_name} • IFSC: {additionalStage.ifsc_code}
              </div>
            </div>

            <div className="bg-white rounded-lg p-2.5 border border-amber-200 text-xs flex items-center justify-between">
              <span className="text-gray-500 font-medium">Cryptographic Seal (HMAC-SHA256):</span>
              <span className="font-mono text-purple-900 font-semibold">
                {additionalStage.cryptographic_seal.slice(0, 16)}...
              </span>
            </div>
          </div>

          <div className="text-center">
            <p className="text-base font-bold text-gray-900">
              {additionalStage.prompt}
            </p>
          </div>

          <form onSubmit={onSubmitAdditionalConfirmation} className="space-y-4">
            {/* Explicit Anti-Fraud Affirmations */}
            <div className="space-y-2 bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm">
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={explicitConfirmed}
                  onChange={(e) => setExplicitConfirmed(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                />
                <span className="text-gray-700">
                  I explicitly verify that I personally initiated this transfer of{" "}
                  <strong>{formatINR(additionalStage.amount)}</strong> to{" "}
                  <strong>{additionalStage.beneficiary_name}</strong>.
                </span>
              </label>

              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={antiCoercionConfirmed}
                  onChange={(e) => setAntiCoercionConfirmed(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                />
                <span className="text-gray-700">
                  I confirm that I am not following instructions from an unknown phone caller, tech support, or screen sharing tool.
                </span>
              </label>
            </div>

            {/* Factor 3: Transaction Security PIN */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-sm font-medium text-gray-700">
                  Transaction Security PIN
                </label>
                <span className="text-xs text-purple-700 font-medium">
                  Default PIN: <strong>1234</strong>
                </span>
              </div>
              <input
                type="password"
                inputMode="numeric"
                maxLength={6}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-center text-xl font-mono tracking-[0.4em] focus:ring-2 focus:ring-purple-500 outline-none"
                value={transactionPin}
                onChange={(e) => setTransactionPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading || !explicitConfirmed || !antiCoercionConfirmed || transactionPin.length < 4}
              className="w-full bg-amber-600 hover:bg-amber-700 text-white py-3 rounded-lg font-bold disabled:opacity-50 transition-colors shadow-sm text-base flex items-center justify-center gap-2"
            >
              <span>🔒</span>
              <span>{loading ? "Cryptographically Signing..." : "Cryptographically Sign & Execute Transfer"}</span>
            </button>
          </form>

          <div className="text-center pt-1">
            <button
              type="button"
              onClick={onCancelFlow}
              className="text-sm text-red-600 hover:underline"
            >
              Cancel Transfer
            </button>
          </div>
        </div>
      )}

      {/* ── STAGE 5: SUCCESS RECEIPT ── */}
      {currentStep === "success" && completedTx && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm text-center space-y-4">
          <div className="w-16 h-16 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center mx-auto text-3xl font-bold">
            ✓
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Transfer Completed!</h2>
          <p className="text-sm text-gray-500">
            Transaction authorized via <strong>Static 3-Factor Authentication</strong>.
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
              <span className="font-bold text-purple-900">{formatINR(completedTx.amount)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Auth Mechanism:</span>
              <span className="text-xs bg-purple-100 text-purple-800 font-semibold px-2 py-0.5 rounded">
                Static 3FA (Password + OTP + Additional Verification)
              </span>
            </div>
            {completedTx.cryptographic_seal && (
              <div className="pt-1 border-t border-gray-200">
                <span className="text-xs text-gray-500 block mb-0.5">Cryptographic Binding Seal:</span>
                <span className="font-mono text-xs text-purple-900 break-all bg-purple-50 p-1.5 rounded block">
                  {completedTx.cryptographic_seal}
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => {
                setCompletedTx(null);
                setChallenge(null);
                setAdditionalStage(null);
                setAmount("");
                setRemark("");
                setTransactionPin("");
                setExplicitConfirmed(false);
                setAntiCoercionConfirmed(false);
                setCurrentStep("details");
              }}
              className="flex-1 bg-purple-700 hover:bg-purple-800 text-white py-2.5 rounded-lg font-medium transition-colors"
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
