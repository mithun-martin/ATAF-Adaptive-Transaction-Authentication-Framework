import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { login } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setToken } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const message = (location.state as { message?: string } | null)?.message;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      // Store OTP display for the verify page
      if (data.otp_display) {
        sessionStorage.setItem("pending_otp", data.otp_display);
        sessionStorage.setItem("otp_phone_msg", data.message);
      }
      navigate("/verify-otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-blue-900">🏦 SimBank</h1>
          <p className="text-sm text-gray-500 mt-1">Simulated Banking Environment</p>
        </div>

        {message && <p className="mb-4 text-sm text-green-700 bg-green-50 p-3 rounded-lg">{message}</p>}
        {error && <p className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 6 characters"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white py-2.5 rounded-lg font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <p className="mt-5 text-sm text-center text-gray-600">
          New user?{" "}
          <Link to="/register" className="text-blue-700 font-medium hover:underline">
            Create account
          </Link>
        </p>
      </div>
    </div>
  );
}
