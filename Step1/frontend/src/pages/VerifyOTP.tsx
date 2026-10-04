import { FormEvent, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { verifyOTP, requestOTP } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function VerifyOTP() {
  const navigate = useNavigate();
  const { token, setOtpVerified, isOtpVerified } = useAuth();
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [simulatedOTP, setSimulatedOTP] = useState<string | null>(null);
  const [phoneMsg, setPhoneMsg] = useState<string>("");
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (isOtpVerified) {
      navigate("/dashboard", { replace: true });
      return;
    }
    // Get the simulated OTP from login response
    const pending = sessionStorage.getItem("pending_otp");
    const msg = sessionStorage.getItem("otp_phone_msg");
    if (pending) setSimulatedOTP(pending);
    if (msg) setPhoneMsg(msg);
  }, [isOtpVerified, navigate]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError("");
    setLoading(true);
    try {
      await verifyOTP(token, code, "LOGIN");
      setOtpVerified(true);
      sessionStorage.removeItem("pending_otp");
      sessionStorage.removeItem("otp_phone_msg");
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "OTP verification failed");
    } finally {
      setLoading(false);
    }
  }

  async function onResend() {
    if (!token) return;
    setResending(true);
    setError("");
    try {
      const resp = await requestOTP(token, "LOGIN");
      setSimulatedOTP(resp.otp_display);
      setPhoneMsg(resp.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend OTP");
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-blue-900">🔐 OTP Verification</h1>
          {phoneMsg && <p className="text-sm text-gray-500 mt-2">{phoneMsg}</p>}
        </div>

        {/* Simulated OTP Display — in a real system this goes via SMS */}
        {simulatedOTP && (
          <div className="mb-5 bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
            <p className="text-xs text-amber-700 font-medium mb-1">⚠ SIMULATED OTP (would be sent via SMS)</p>
            <p className="text-3xl font-mono font-bold tracking-widest text-amber-900">
              {simulatedOTP}
            </p>
          </div>
        )}

        {error && <p className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Enter OTP</label>
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              className="w-full border border-gray-300 rounded-lg px-3 py-3 text-center text-2xl font-mono tracking-[0.5em] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="000000"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading || code.length !== 6}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white py-2.5 rounded-lg font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? "Verifying..." : "Verify OTP"}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={onResend}
            disabled={resending}
            className="text-sm text-blue-700 hover:underline disabled:opacity-50"
          >
            {resending ? "Sending..." : "Resend OTP"}
          </button>
        </div>
      </div>
    </div>
  );
}
