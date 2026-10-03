import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { formatINR, getAccount, getTransactions, type Account, type Transaction } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { token } = useAuth();
  const [account, setAccount] = useState<Account | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    Promise.all([getAccount(token), getTransactions(token)])
      .then(([acc, txs]) => {
        setAccount(acc);
        setTransactions(txs.slice(0, 5));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"));
  }, [token]);

  if (error) {
    return <p className="text-red-600 bg-red-50 p-3 rounded">{error}</p>;
  }

  if (!account) {
    return <p className="text-gray-500">Loading dashboard...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome, {account.user_name}</h1>
        <p className="text-gray-500 text-sm mt-1">Your simulated bank account overview</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <p className="text-sm text-gray-500">Account Number</p>
        <p className="text-lg font-medium">{account.account_number}</p>
        <p className="text-sm text-gray-500 mt-4">Balance</p>
        <p className="text-3xl font-semibold text-blue-800">{formatINR(account.balance)}</p>
        <Link
          to="/transfer"
          className="inline-block mt-5 bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded"
        >
          Send Money
        </Link>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-medium">Recent Transactions</h2>
          <Link to="/transactions" className="text-sm text-blue-700 hover:underline">
            View all
          </Link>
        </div>
        {transactions.length === 0 ? (
          <p className="text-sm text-gray-500">No transactions yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="py-2 pr-2">Date</th>
                  <th className="py-2 pr-2">Beneficiary</th>
                  <th className="py-2 pr-2">Amount</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id} className="border-b border-gray-100">
                    <td className="py-2 pr-2">{new Date(tx.created_at).toLocaleString()}</td>
                    <td className="py-2 pr-2">{tx.beneficiary_name}</td>
                    <td className="py-2 pr-2">{formatINR(tx.amount)}</td>
                    <td className="py-2">
                      <span
                        className={
                          tx.status === "COMPLETED" ? "text-green-700" : "text-red-600"
                        }
                      >
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
