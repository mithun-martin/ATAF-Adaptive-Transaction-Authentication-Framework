import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type AuthState = {
  token: string | null;
  isOtpVerified: boolean;
  setToken: (token: string) => void;
  setOtpVerified: (v: boolean) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);
const TOKEN_KEY = "bank_token";
const OTP_KEY = "bank_otp_verified";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [isOtpVerified, setOtpVerifiedState] = useState<boolean>(
    () => localStorage.getItem(OTP_KEY) === "true",
  );

  const value = useMemo<AuthState>(
    () => ({
      token,
      isOtpVerified,
      setToken: (t: string) => {
        localStorage.setItem(TOKEN_KEY, t);
        localStorage.removeItem(OTP_KEY);
        setTokenState(t);
        setOtpVerifiedState(false);
      },
      setOtpVerified: (v: boolean) => {
        if (v) {
          localStorage.setItem(OTP_KEY, "true");
        } else {
          localStorage.removeItem(OTP_KEY);
        }
        setOtpVerifiedState(v);
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(OTP_KEY);
        setTokenState(null);
        setOtpVerifiedState(false);
      },
    }),
    [token, isOtpVerified],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
