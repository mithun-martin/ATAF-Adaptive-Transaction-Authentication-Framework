import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { token, isOtpVerified, logout } = useAuth();
  const navigate = useNavigate();

  function onLogout() {
    logout();
    navigate("/login");
  }

  if (!token || !isOtpVerified) {
    return null;
  }

  return (
    <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40 backdrop-blur-md bg-opacity-90">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-2">
              <span className="text-xl font-bold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
                ATAF Bank
              </span>
            </Link>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
              System 3: Adaptive AI
            </span>
          </div>

          <div className="hidden md:flex space-x-6">
            <Link to="/" className="text-slate-300 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
              Dashboard
            </Link>
            <Link to="/transfer" className="text-emerald-400 hover:text-emerald-300 px-3 py-2 text-sm font-semibold transition-colors">
              Transfer Money
            </Link>
            <Link to="/beneficiaries" className="text-slate-300 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
              Beneficiaries
            </Link>
            <Link to="/transactions" className="text-slate-300 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
              History
            </Link>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onLogout}
              className="text-slate-400 hover:text-rose-400 text-sm font-medium px-3 py-1.5 rounded-lg border border-slate-800 hover:border-rose-900/50 hover:bg-rose-950/20 transition-all"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
