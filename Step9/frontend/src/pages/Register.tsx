import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/client";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [pin, setPin] = useState("1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(name, email, phone, password, pin);
      navigate("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white">Create Account</h2>
          <p className="text-xs text-emerald-400 mt-1">Get ₹100,000 simulated balance for ATAF testing</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Full Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Aritra Sen"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="aritra@example.com"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Mobile Number</label>
            <input
              type="tel"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+919876543210"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Account Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              4-Digit Transaction Security PIN (for High-Risk Step-Up 3FA)
            </label>
            <input
              type="password"
              maxLength={4}
              required
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="1234"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-white font-mono tracking-widest text-center placeholder-slate-600 focus:outline-none focus:border-emerald-500 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl transition-all shadow-lg shadow-emerald-950 disabled:opacity-50 mt-4"
          >
            {loading ? "Registering..." : "Create Account"}
          </button>
        </form>

        <div className="mt-4 text-center text-xs text-slate-400">
          Already registered?{" "}
          <Link to="/login" className="text-emerald-400 hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
