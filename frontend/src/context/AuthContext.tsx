import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type AuthState = {
  token: string | null;
  setToken: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);
const TOKEN_KEY = "bank_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));

  const value = useMemo<AuthState>(
    () => ({
      token,
      setToken: (t: string) => {
        localStorage.setItem(TOKEN_KEY, t);
        localStorage.removeItem("bank_otp_verified");
        setTokenState(t);
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem("bank_otp_verified");
        setTokenState(null);
      },
    }),
    [token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
