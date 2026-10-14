import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login, verifyLoginOTP } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [tempToken, setTempToken] = useState<string | null>(null);
  const [otpDisplay, setOtpDisplay] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { setToken, setOtpVerified } = useAuth();
  const navigate = useNavigate();

  async function handlePasswordSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      setTempToken(res.access_token);
      setToken(res.access_token);
      if (res.requires_otp) {
        setOtpDisplay(res.otp_display || null);
      } else {
        setOtpVerified(true);
        navigate("/");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sign in");
    } finally {
      setLoading(false);
    }
  }

  async function handleOTPSubmit(e: FormEvent) {
    e.preventDefault();
    if (!tempToken) return;
    setError("");
    setLoading(true);
    try {
      await verifyLoginOTP(otpCode, tempToken);
      setOtpVerified(true);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid verification code");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 mb-3">
            <span className="text-2xl">🛡️</span>
          </div>
          <h2 className="text-2xl font-bold text-white">ATAF Bank</h2>
          <p className="text-sm text-emerald-400 font-medium mt-1">System 3: Proposed Adaptive Authentication</p>
          <p className="text-xs text-slate-400 mt-2">Sign in to access your secure simulated account</p>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
            {error}
          </div>
        )}

        {!tempToken ? (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Account Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl transition-all shadow-lg shadow-emerald-950 disabled:opacity-50 mt-2"
            >
              {loading ? "Authenticating..." : "Continue to 2FA"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleOTPSubmit} className="space-y-4">
            <div className="bg-emerald-950/30 border border-emerald-800/40 rounded-xl p-3 text-center">
              <span className="text-xs text-emerald-300 font-medium">Factor 2: Out-of-Band OTP Dispatched</span>
              {otpDisplay && (
                <div className="mt-2 text-2xl font-mono tracking-widest text-emerald-400 font-bold">
                  {otpDisplay}
                </div>
              )}
              <p className="text-[11px] text-slate-400 mt-1">Simulated delivery for testing environment</p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Enter 6-Digit OTP
              </label>
              <input
                type="text"
                maxLength={6}
                required
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                placeholder="123456"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-center text-xl font-mono tracking-widest text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading || otpCode.length !== 6}
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl transition-all disabled:opacity-50"
            >
              {loading ? "Verifying..." : "Confirm & Sign In"}
            </button>
          </form>
        )}

        <div className="mt-6 text-center text-xs text-slate-400">
          Don't have an account?{" "}
          <Link to="/register" className="text-emerald-400 hover:underline font-medium">
            Create account
          </Link>
        </div>
      </div>
    </div>
  );
}
