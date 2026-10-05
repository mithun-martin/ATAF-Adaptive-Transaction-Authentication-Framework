import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { formatINR, getTransactions, type Transaction } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Transactions() {
  const { token } = useAuth();
  const location = useLocation();
  const [rows, setRows] = useState<Transaction[]>([]);
  const [error, setError] = useState("");
  const message = (location.state as { message?: string } | null)?.message;

  useEffect(() => {
    if (!token) return;
    getTransactions(token)
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [token]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transaction History</h1>
        <p className="text-sm text-gray-500 mt-1">
          All transfers authenticated via Static 3-Factor Authentication (Password + OTP + Additional Verification)
        </p>
      </div>

      {message && <p className="text-sm text-green-700 bg-green-50 p-3 rounded-lg border border-green-200">{message}</p>}
      {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">{error}</p>}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        {rows.length === 0 ? (
          <p className="text-sm text-gray-500 p-6 text-center">No transactions yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b bg-gray-50">
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Reference</th>
                  <th className="py-3 px-4">Beneficiary</th>
                  <th className="py-3 px-4">Account</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Auth Mechanism</th>
                  <th className="py-3 px-4">Cryptographic Seal</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((tx) => (
                  <tr key={tx.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-600 whitespace-nowrap">
                      {new Date(tx.created_at).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-gray-500">{tx.reference_id}</td>
                    <td className="py-3 px-4 font-medium">
                      {tx.beneficiary_name}
                      {tx.remark && <p className="text-xs text-gray-400">{tx.remark}</p>}
                    </td>
                    <td className="py-3 px-4 font-mono text-sm">{tx.beneficiary_account}</td>
                    <td className="py-3 px-4 font-bold text-gray-900">{formatINR(tx.amount)}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">
                        <span>🛡️</span>
                        Static 3FA (3 Factors)
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-purple-900">
                      {tx.cryptographic_seal ? (
                        <span title={tx.cryptographic_seal} className="bg-gray-100 px-1.5 py-0.5 rounded">
                          {tx.cryptographic_seal.slice(0, 10)}...
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          tx.status === "COMPLETED"
                            ? "bg-green-100 text-green-800"
                            : tx.status === "PENDING"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {tx.status}
                      </span>
                      {tx.failure_reason && (
                        <p className="text-xs text-red-500 mt-1">{tx.failure_reason}</p>
                      )}
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
