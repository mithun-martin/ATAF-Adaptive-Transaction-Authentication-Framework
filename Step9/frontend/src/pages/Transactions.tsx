import { useEffect, useState } from "react";
import { formatINR, getTransactions, type Transaction } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Transactions() {
  const { token } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);

  useEffect(() => {
    if (!token) return;
    getTransactions(token)
      .then(setTransactions)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load transactions"))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Transaction Audit Trail</h2>
        <p className="text-xs text-slate-400 mt-1">
          Detailed cryptographic records of all adaptive transaction decisions and authentication factor enforcement.
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading audit records...</div>
      ) : transactions.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-400">
          No transactions found.
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Reference ID</th>
                  <th className="px-6 py-3">Recipient</th>
                  <th className="px-6 py-3">Amount</th>
                  <th className="px-6 py-3">Risk Assessment</th>
                  <th className="px-6 py-3">Factors Enforced</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-slate-300">{tx.reference_id}</td>
                    <td className="px-6 py-4 font-medium text-white">{tx.beneficiary_name}</td>
                    <td className="px-6 py-4 font-semibold text-white">{formatINR(tx.amount)}</td>
                    <td className="px-6 py-4">
                      {tx.risk_tier === "LOW" && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                          🟢 LOW ({tx.risk_score.toFixed(2)})
                        </span>
                      )}
                      {tx.risk_tier === "MEDIUM" && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950 text-amber-400 border border-amber-800">
                          🟡 MEDIUM ({tx.risk_score.toFixed(2)})
                        </span>
                      )}
                      {tx.risk_tier === "HIGH" && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950 text-rose-400 border border-rose-800">
                          🔴 HIGH ({tx.risk_score.toFixed(2)})
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">{tx.auth_factors}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-400">
                        {tx.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => setSelectedTx(tx)}
                        className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold underline"
                      >
                        Receipt
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transaction Audit Receipt Modal */}
      {selectedTx && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-start border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white">ATAF Audit Receipt</h3>
                <p className="text-xs font-mono text-slate-400 mt-0.5">{selectedTx.reference_id}</p>
              </div>
              <button
                onClick={() => setSelectedTx(null)}
                className="text-slate-500 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Recipient:</span>
                <span className="text-white font-medium">{selectedTx.beneficiary_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Account:</span>
                <span className="text-white font-mono">{selectedTx.beneficiary_account}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Amount:</span>
                <span className="text-white font-semibold text-sm">{formatINR(selectedTx.amount)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">AI Risk Score:</span>
                <span className="text-white font-mono font-semibold">
                  {selectedTx.risk_score.toFixed(4)} ({selectedTx.risk_tier})
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Auth Factors:</span>
                <span className="text-emerald-400 font-mono font-semibold">{selectedTx.auth_factors}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Framework Mode:</span>
                <span className="text-slate-200 font-medium">{selectedTx.auth_mode}</span>
              </div>
              {selectedTx.cryptographic_seal && (
                <div className="py-2 bg-slate-950 rounded-xl p-3 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-semibold uppercase tracking-wider mb-1">
                    PSD2 Art. 97 HMAC-SHA256 Cryptographic Seal
                  </span>
                  <div className="font-mono text-[10px] text-emerald-400 break-all">
                    {selectedTx.cryptographic_seal}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-2">
              <button
                onClick={() => setSelectedTx(null)}
                className="w-full bg-slate-800 hover:bg-slate-700 text-white font-semibold py-2 rounded-xl text-xs transition-colors"
              >
                Close Receipt
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
