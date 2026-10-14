import { FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  confirmHighRiskTransaction,
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
  type TransactionVerificationResponse,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

type FlowStep = "details" | "otp" | "high_risk_step_up" | "success";

export default function Transfer() {
  const { token } = useAuth();
  const [searchParams] = useSearchParams();

  // Banking State
  const [account, setAccount] = useState<Account | null>(null);
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [beneficiaryId, setBeneficiaryId] = useState(searchParams.get("ben") || "");
  const [amount, setAmount] = useState("");
  const [remark, setRemark] = useState("");
  const [password, setPassword] = useState("");

  // Flow & Challenge State
  const [currentStep, setCurrentStep] = useState<FlowStep>("details");
  const [challenge, setChallenge] = useState<TransactionChallengeResponse | null>(null);
  const [otpCode, setOtpCode] = useState("");
  const [stepUpData, setStepUpData] = useState<TransactionVerificationResponse | null>(null);

  // High-Risk Step-Up Factor 3 State
  const [transactionPin, setTransactionPin] = useState("");
  const [explicitAffirmation, setExplicitAffirmation] = useState(false);
  const [antiCoercionAck, setAntiCoercionAck] = useState(false);
  const [nonRefundableAck, setNonRefundableAck] = useState(false);

  // Success State
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
        if (!beneficiaryId && bens.length > 0) {
          setBeneficiaryId(String(bens[0].id));
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load account data"));
  }, [token]);

  const selectedBeneficiary = beneficiaries.find((b) => String(b.id) === beneficiaryId);

  // ── Step 1: Initiate Transfer (Factor 1 - Password Auth + AI Risk Assessment) ──
  async function handleInitiate(e: FormEvent) {
    e.preventDefault();
    if (!token || !selectedBeneficiary) return;

    const val = Number(amount);
    if (!val || val <= 0) {
      setError("Please enter a valid amount.");
      return;
    }
    if (account && val > account.balance) {
      setError(`Insufficient balance. Available: ${formatINR(account.balance)}`);
      return;
    }
    if (!password) {
      setError("Account password is required for Factor 1 authentication.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const challengeResp = await initiateTransaction(token, {
        beneficiary_id: selectedBeneficiary.id,
        amount: val,
        remark: remark || undefined,
        password: password,
      });

      setChallenge(challengeResp);
      setPassword(""); // Clear password for security
      setCurrentStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Initiation failed");
    } finally {
      setLoading(false);
    }
  }

  // ── Step 2: Verify OTP (Factor 2 + Dynamic Routing) ──
  async function handleVerifyOTP(e: FormEvent) {
    e.preventDefault();
    if (!token || !challenge) return;
    if (otpCode.length !== 6) {
      setError("Please enter a 6-digit OTP code.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const verifyResp = await verifyTransactionOTP(token, challenge.challenge_id, otpCode);

      if (verifyResp.requires_step_up) {
        // High Risk Tier: Advance to Step 8 Transaction-Bound Verification!
        setStepUpData(verifyResp);
        setCurrentStep("high_risk_step_up");
      } else if (verifyResp.transaction) {
        // Low or Medium Risk: Transaction authorized and completed immediately!
        setCompletedTx(verifyResp.transaction);
        setCurrentStep("success");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "OTP verification failed");
    } finally {
      setLoading(false);
    }
  }

  // ── Step 3: High-Risk Step-Up Confirmation (Factor 3 - Seal + Affirmation + PIN) ──
  async function handleHighRiskConfirm(e: FormEvent) {
    e.preventDefault();
    if (!token || !challenge) return;

    if (!explicitAffirmation) {
      setError("You must explicitly verify you personally initiated this transaction.");
      return;
    }
    if (!antiCoercionAck) {
      setError("You must acknowledge that you are not under coercion from a phone caller or third party.");
      return;
    }
    if (!nonRefundableAck) {
      setError("You must acknowledge that this high-risk transfer is final and non-refundable.");
      return;
    }
    if (!transactionPin || transactionPin.length < 4) {
      setError("Please enter your 4-digit Transaction Security PIN.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const tx = await confirmHighRiskTransaction(token, {
        challenge_id: challenge.challenge_id,
        transaction_pin: transactionPin,
        explicit_affirmation: true,
        anti_coercion_ack: true,
      });

      setCompletedTx(tx);
      setCurrentStep("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "High-risk authorization failed");
    } finally {
      setLoading(false);
    }
  }

  // ── Resend OTP Helper ──
  async function handleResend() {
    if (!token || !challenge) return;
    setResending(true);
    try {
      const newChal = await resendTransactionOTP(token, challenge.challenge_id);
      setChallenge(newChal);
      setOtpCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend OTP");
    } finally {
      setResending(false);
    }
  }

  function resetForm() {
    setCurrentStep("details");
    setChallenge(null);
    setStepUpData(null);
    setCompletedTx(null);
    setAmount("");
    setRemark("");
    setPassword("");
    setOtpCode("");
    setTransactionPin("");
    setExplicitAffirmation(false);
    setAntiCoercionAck(false);
    setNonRefundableAck(false);
    setError("");
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10 space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-xs text-emerald-400 font-semibold mb-2">
          <span>🛡️ Proposed System 3: Adaptive Multi-Factor Pipeline</span>
        </div>
        <h2 className="text-3xl font-extrabold text-white">Transfer Money</h2>
        <p className="text-xs text-slate-400 mt-1">
          Dynamic security policy continuously monitors behavioural anomalies and escalates friction only when fraud risk is detected.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* ─── STAGE 1: TRANSACTION DETAILS ──────────────────────────────────── */}
      {currentStep === "details" && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <form onSubmit={handleInitiate} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Select Beneficiary
              </label>
              {beneficiaries.length === 0 ? (
                <div className="text-xs text-slate-500 py-2">
                  No beneficiaries found.{" "}
                  <Link to="/beneficiaries" className="text-emerald-400 underline">
                    Add one first
                  </Link>
                </div>
              ) : (
                <select
                  value={beneficiaryId}
                  onChange={(e) => setBeneficiaryId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  {beneficiaries.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.bank_name} - {b.account_number.slice(-4)})
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Transfer Amount (INR)
                </label>
                {account && (
                  <span className="text-[11px] text-slate-400">
                    Available: <strong className="text-slate-200">{formatINR(account.balance)}</strong>
                  </span>
                )}
              </div>
              <div className="relative">
                <span className="absolute left-4 top-2.5 text-slate-500 font-semibold">₹</span>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-4 py-2.5 text-white text-lg font-semibold focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Remark (Optional)
              </label>
              <input
                type="text"
                value={remark}
                onChange={(e) => setRemark(e.target.value)}
                placeholder="e.g. Rent, Groceries, Consultant fees"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="pt-2 border-t border-slate-800">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Factor 1: Account Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Verify account password"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Submitting executes the AI risk assessment & policy evaluation.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || beneficiaries.length === 0}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-xl transition-all shadow-lg shadow-emerald-950 disabled:opacity-50 mt-4 text-sm"
            >
              {loading ? "Evaluating AI Risk & Initiating..." : "Initiate Adaptive Transfer →"}
            </button>
          </form>
        </div>
      )}

      {/* ─── STAGE 2: AI RISK ASSESSMENT & FACTOR 2 OTP ────────────────────── */}
      {currentStep === "otp" && challenge && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          {/* Dynamic AI Risk Card */}
          <div className={`p-4 rounded-xl border ${
            challenge.risk_tier === "LOW"
              ? "bg-emerald-950/30 border-emerald-800/60"
              : challenge.risk_tier === "MEDIUM"
              ? "bg-amber-950/30 border-amber-800/60"
              : "bg-rose-950/30 border-rose-800/60"
          }`}>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                AI Risk Inference Evaluation
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                challenge.risk_tier === "LOW"
                  ? "bg-emerald-900 text-emerald-300"
                  : challenge.risk_tier === "MEDIUM"
                  ? "bg-amber-900 text-amber-300"
                  : "bg-rose-900 text-rose-300"
              }`}>
                {challenge.risk_tier === "LOW" && "🟢 LOW RISK"}
                {challenge.risk_tier === "MEDIUM" && "🟡 MEDIUM RISK"}
                {challenge.risk_tier === "HIGH" && "🔴 HIGH RISK"}
                {" "}({challenge.risk_score.toFixed(4)})
              </span>
            </div>

            {challenge.warning_banner && (
              <div className="mt-2 p-3 rounded-lg bg-black/40 text-xs leading-relaxed text-slate-200 border border-slate-800">
                {challenge.warning_banner}
              </div>
            )}

            {challenge.risk_reasons.length > 0 && (
              <div className="mt-3 space-y-1">
                <span className="text-[11px] font-semibold text-slate-400">Flagged Risk Indicators:</span>
                <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
                  {challenge.risk_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-3 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
              {challenge.risk_tier === "LOW" && "Routine transaction: Verifying OTP authorizes the transfer directly with zero friction."}
              {challenge.risk_tier === "MEDIUM" && "Advisory Tier: Review warning above carefully before entering OTP."}
              {challenge.risk_tier === "HIGH" && "Critical Tier: Entering OTP will advance directly to Step 8 Transaction-Bound 3FA."}
            </div>
          </div>

          {/* OTP Box */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-center">
            <span className="text-xs text-slate-400">Simulated Out-of-Band Delivery (Test Environment)</span>
            <div className="text-2xl font-mono tracking-widest text-emerald-400 font-bold mt-1">
              {challenge.otp_display}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Sent to registered phone {challenge.masked_phone}
            </p>
          </div>

          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Enter 6-Digit OTP (Factor 2)
              </label>
              <input
                type="text"
                maxLength={6}
                required
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                placeholder="123456"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-center text-2xl font-mono tracking-widest text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="flex space-x-3">
              <button
                type="button"
                onClick={resetForm}
                className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-2.5 rounded-xl text-sm transition-colors"
              >
                Cancel Transfer
              </button>
              <button
                type="submit"
                disabled={loading || otpCode.length !== 6}
                className="flex-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-emerald-950 disabled:opacity-50"
              >
                {loading ? "Verifying OTP..." : "Verify OTP & Continue →"}
              </button>
            </div>
          </form>

          <div className="text-center">
            <button
              onClick={handleResend}
              disabled={resending}
              className="text-xs text-slate-400 hover:text-emerald-400 underline"
            >
              {resending ? "Generating fresh OTP..." : "Resend OTP"}
            </button>
          </div>
        </div>
      )}

      {/* ─── STAGE 3: HIGH-RISK STEP-UP (STEP 8 TRANSACTION-BOUND VERIFICATION) ── */}
      {currentStep === "high_risk_step_up" && stepUpData && (
        <div className="bg-slate-900 border border-rose-900/60 rounded-2xl p-6 shadow-2xl space-y-6">
          <div className="border-b border-rose-900/40 pb-4">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-950 text-rose-300 border border-rose-800">
              Factor 3: PSD2 Art. 97 Transaction Binding
            </span>
            <h3 className="text-xl font-bold text-white mt-2">High-Risk Transaction Confirmation</h3>
            <p className="text-xs text-rose-300/80 mt-1">
              Due to severe fraud risk indicators, you must explicitly review locked parameters and authenticate with your Security PIN.
            </p>
          </div>

          {/* Locked Parameters Card */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Locked Transfer Amount:</span>
              <span className="text-lg font-bold text-rose-400 font-mono">
                {stepUpData.amount ? formatINR(stepUpData.amount) : "₹0.00"}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Designated Payee:</span>
              <span className="text-white font-semibold">{stepUpData.beneficiary_name}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/80">
              <span className="text-slate-400">Destination Account:</span>
              <span className="text-white font-mono">{stepUpData.beneficiary_account}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Bank & IFSC:</span>
              <span className="text-slate-300 font-mono">{stepUpData.bank_name} ({stepUpData.ifsc_code})</span>
            </div>
          </div>

          {/* Cryptographic Parameter Seal Badge */}
          {stepUpData.cryptographic_seal && (
            <div className="p-3 bg-black/50 border border-slate-800 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block mb-1">
                HMAC-SHA256 Cryptographic Parameter Binding Seal
              </span>
              <div className="font-mono text-[10px] text-emerald-400 break-all">
                {stepUpData.cryptographic_seal}
              </div>
            </div>
          )}

          {/* Affirmation Checkboxes */}
          <form onSubmit={handleHighRiskConfirm} className="space-y-4">
            <div className="space-y-3 p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs">
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={explicitAffirmation}
                  onChange={(e) => setExplicitAffirmation(e.target.checked)}
                  className="mt-0.5 rounded text-emerald-500 focus:ring-emerald-400"
                />
                <span className="text-slate-200">
                  I explicitly confirm I am transferring {stepUpData.amount ? formatINR(stepUpData.amount) : ""} to {stepUpData.beneficiary_name}.
                </span>
              </label>

              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={antiCoercionAck}
                  onChange={(e) => setAntiCoercionAck(e.target.checked)}
                  className="mt-0.5 rounded text-emerald-500 focus:ring-emerald-400"
                />
                <span className="text-slate-200">
                  I confirm that I am NOT acting under instructions from an unknown caller, fake law enforcement officer, or remote access app (AnyDesk, TeamViewer).
                </span>
              </label>

              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={nonRefundableAck}
                  onChange={(e) => setNonRefundableAck(e.target.checked)}
                  className="mt-0.5 rounded text-emerald-500 focus:ring-emerald-400"
                />
                <span className="text-slate-200">
                  I acknowledge that this transfer is authentic, final, and non-reversible.
                </span>
              </label>
            </div>

            {/* 4-Digit Security PIN */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                4-Digit Transaction Security PIN
              </label>
              <input
                type="password"
                maxLength={4}
                required
                value={transactionPin}
                onChange={(e) => setTransactionPin(e.target.value)}
                placeholder="••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-center text-xl font-mono tracking-widest text-white focus:outline-none focus:border-rose-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">Default test PIN is 1234 or your registered PIN.</p>
            </div>

            <div className="flex space-x-3 pt-2">
              <button
                type="button"
                onClick={resetForm}
                className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-2.5 rounded-xl text-sm"
              >
                Abort Transfer
              </button>
              <button
                type="submit"
                disabled={loading || !explicitAffirmation || !antiCoercionAck || !nonRefundableAck || transactionPin.length < 4}
                className="flex-2 bg-rose-600 hover:bg-rose-500 text-white font-semibold py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-rose-950 disabled:opacity-50"
              >
                {loading ? "Authenticating Seal & PIN..." : "Authorize High-Risk Transfer"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ─── STAGE 4: SUCCESS RECEIPT ──────────────────────────────────────── */}
      {currentStep === "success" && completedTx && (
        <div className="bg-slate-900 border border-emerald-800/80 rounded-2xl p-8 shadow-2xl text-center space-y-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-3xl">
            ✓
          </div>

          <div>
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Transaction Successfully Authorized
            </span>
            <h3 className="text-3xl font-extrabold text-white mt-1">
              {formatINR(completedTx.amount)}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Transferred to <strong className="text-white">{completedTx.beneficiary_name}</strong>
            </p>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2 text-left max-w-md mx-auto">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Reference:</span>
              <span className="text-slate-200 font-mono font-medium">{completedTx.reference_id}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Risk Assessment:</span>
              <span className="text-slate-200 font-medium">
                {completedTx.risk_tier} (R = {completedTx.risk_score.toFixed(4)})
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Factors Enforced:</span>
              <span className="text-emerald-400 font-mono font-medium">{completedTx.auth_factors}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Framework Policy:</span>
              <span className="text-slate-200 font-medium">{completedTx.auth_mode}</span>
            </div>
          </div>

          <div className="flex space-x-3 justify-center pt-2">
            <button
              onClick={resetForm}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-all"
            >
              Send Another Transfer
            </button>
            <Link
              to="/transactions"
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold px-6 py-2.5 rounded-xl text-sm transition-all"
            >
              View Audit Log
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
