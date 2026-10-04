import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Navbar from "./Navbar";

export function PublicOnly({ children }: { children: React.ReactNode }) {
  const { token, isOtpVerified } = useAuth();
  if (token && isOtpVerified) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export function RequireAuth() {
  const { token, isOtpVerified } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  if (!isOtpVerified) return <Navigate to="/verify-otp" replace />;
  return (
    <>
      <Navbar />
      <main className="max-w-5xl mx-auto p-4 md:p-6">
        <Outlet />
      </main>
    </>
  );
}

export function RequireToken() {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return <Outlet />;
}
