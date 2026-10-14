import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  formatINR,
  getAccount,
  getTransactions,
  type Account,
  type Transaction,
} from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { token } = useAuth();
  const [account, setAccount] = useState<Account | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    Promise.all([getAccount(token), getTransactions(token)])
      .then(([acc, txs]) => {
        setAccount(acc);
        setTransactions(txs.slice(0, 5));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center text-slate-400">
        Loading ATAF banking dashboard...
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Account Balance Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full filter blur-3xl pointer-events-none" />
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                Simulated Checking Account
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white mt-2">
                {account ? formatINR(account.balance) : "₹0.00"}
              </h2>
            </div>
            <Link
              to="/transfer"
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-5 py-2.5 rounded-xl transition-all shadow-lg shadow-emerald-950 text-sm inline-flex items-center space-x-2"
            >
              <span>Initiate Transfer</span>
              <span>→</span>
            </Link>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-slate-400 block">Account Holder</span>
              <span className="text-slate-200 font-medium">{account?.user_name}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Account Number</span>
              <span className="text-slate-200 font-mono font-medium">{account?.account_number}</span>
            </div>
            <div>
              <span className="text-slate-400 block">IFSC Code</span>
              <span className="text-slate-200 font-mono font-medium">{account?.ifsc_code}</span>
            </div>
          </div>
        </div>

        {/* Framework Architecture Overview */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>System 3: Adaptive Policy Engine</span>
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Dynamically evaluates transaction risk in real time using the calibrated <strong>XGBoost model</strong> from Step 5 & 6.
            </p>

            <div className="mt-4 space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-950/20 border border-emerald-900/30">
                <span className="text-emerald-400 font-medium">🟢 Low (&lt; 0.30)</span>
                <span className="text-slate-300">Password + OTP</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-amber-950/20 border border-amber-900/30">
                <span className="text-amber-400 font-medium">🟡 Medium (0.30-0.70)</span>
                <span className="text-slate-300">Warning + OTP</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-rose-950/20 border border-rose-900/30">
                <span className="text-rose-400 font-medium">🔴 High (&ge; 0.70)</span>
                <span className="text-slate-300">Step 8 3FA Seal + PIN</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
            PSD2 RTS Art. 97 & NIST SP 800-63B Compliant
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-base font-bold text-white">Recent Transactions</h3>
          <Link to="/transactions" className="text-xs text-emerald-400 hover:underline">
            View full history →
          </Link>
        </div>

        {transactions.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            No transactions initiated yet. Send your first transfer to test the adaptive engine!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="pb-3">Reference</th>
                  <th className="pb-3">Recipient</th>
                  <th className="pb-3">Amount</th>
                  <th className="pb-3">Risk Tier</th>
                  <th className="pb-3">Auth Factors</th>
                  <th className="pb-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 font-mono text-xs text-slate-300">{tx.reference_id}</td>
                    <td className="py-3 text-white font-medium">{tx.beneficiary_name}</td>
                    <td className="py-3 font-semibold text-white">{formatINR(tx.amount)}</td>
                    <td className="py-3">
                      {tx.risk_tier === "LOW" && (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                          🟢 LOW ({tx.risk_score.toFixed(2)})
                        </span>
                      )}
                      {tx.risk_tier === "MEDIUM" && (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">
                          🟡 MEDIUM ({tx.risk_score.toFixed(2)})
                        </span>
                      )}
                      {tx.risk_tier === "HIGH" && (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
                          🔴 HIGH ({tx.risk_score.toFixed(2)})
                        </span>
                      )}
                    </td>
                    <td className="py-3 font-mono text-xs text-slate-400">{tx.auth_factors}</td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400">
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
