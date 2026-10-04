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
    return <p className="text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>;
  }

  if (!account) {
    return <p className="text-gray-500">Loading dashboard...</p>;
  }

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome, {account.user_name}</h1>
        <p className="text-gray-500 text-sm mt-1">Your simulated bank account overview</p>
      </div>

      {/* Account Cards */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-blue-800 to-blue-950 text-white rounded-xl p-6">
          <p className="text-blue-200 text-sm">Available Balance</p>
          <p className="text-3xl font-bold mt-1">{formatINR(account.balance)}</p>
          <div className="mt-4 space-y-1 text-sm text-blue-200">
            <p>A/C: {account.account_number}</p>
            <p>IFSC: {account.ifsc_code}</p>
            <p>Phone: {account.masked_phone}</p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <p className="text-gray-500 text-sm">Quick Actions</p>
          </div>
          <div className="mt-4 flex flex-col gap-3">
            <Link
              to="/transfer"
              className="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2.5 rounded-lg text-center font-medium transition-colors"
            >
              💸 Send Money
            </Link>
            <Link
              to="/beneficiaries"
              className="border border-gray-300 hover:bg-gray-50 px-4 py-2.5 rounded-lg text-center font-medium transition-colors"
            >
              👤 Manage Beneficiaries
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Transactions</h2>
          <Link to="/transactions" className="text-sm text-blue-700 hover:underline">
            View all →
          </Link>
        </div>
        {transactions.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">No transactions yet. Send money to get started!</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="py-2 pr-3">Date</th>
                  <th className="py-2 pr-3">Beneficiary</th>
                  <th className="py-2 pr-3">Amount</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id} className="border-b border-gray-100">
                    <td className="py-2.5 pr-3 text-gray-600">
                      {new Date(tx.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                    </td>
                    <td className="py-2.5 pr-3 font-medium">{tx.beneficiary_name}</td>
                    <td className="py-2.5 pr-3 font-medium text-red-700">- {formatINR(tx.amount)}</td>
                    <td className="py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          tx.status === "COMPLETED"
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }`}
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
