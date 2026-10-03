import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { logout } = useAuth();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded text-sm ${isActive ? "bg-blue-700 text-white" : "text-blue-100 hover:bg-blue-800"}`;

  return (
    <nav className="bg-blue-900 text-white px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <Link to="/dashboard" className="font-semibold text-lg tracking-tight">
        🏦 SimBank
      </Link>
      <div className="flex flex-wrap items-center gap-1">
        <NavLink to="/dashboard" className={linkClass}>
          Dashboard
        </NavLink>
        <NavLink to="/beneficiaries" className={linkClass}>
          Beneficiaries
        </NavLink>
        <NavLink to="/transfer" className={linkClass}>
          Transfer
        </NavLink>
        <NavLink to="/transactions" className={linkClass}>
          Transactions
        </NavLink>
        <NavLink to="/profile" className={linkClass}>
          Profile
        </NavLink>
        <button
          onClick={logout}
          className="ml-2 px-3 py-2 rounded text-sm bg-red-600 hover:bg-red-700"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
