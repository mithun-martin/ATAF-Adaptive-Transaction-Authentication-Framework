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
        <h1 className="text-2xl font-semibold">Transaction History</h1>
        <p className="text-sm text-gray-500 mt-1">All transfers from your account.</p>
      </div>

      {message && <p className="text-sm text-green-700 bg-green-50 p-2 rounded">{message}</p>}
      {error && <p className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</p>}

      <div className="bg-white border border-gray-200 rounded-lg p-5 overflow-x-auto">
        {rows.length === 0 ? (
          <p className="text-sm text-gray-500">No transactions yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2 pr-3">Date</th>
                <th className="py-2 pr-3">Beneficiary</th>
                <th className="py-2 pr-3">Account</th>
                <th className="py-2 pr-3">Amount</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((tx) => (
                <tr key={tx.id} className="border-b border-gray-100">
                  <td className="py-2 pr-3">{new Date(tx.created_at).toLocaleString()}</td>
                  <td className="py-2 pr-3">{tx.beneficiary_name}</td>
                  <td className="py-2 pr-3">{tx.beneficiary_account}</td>
                  <td className="py-2 pr-3">{formatINR(tx.amount)}</td>
                  <td className="py-2">
                    <span className={tx.status === "COMPLETED" ? "text-green-700" : "text-red-600"}>
                      {tx.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
