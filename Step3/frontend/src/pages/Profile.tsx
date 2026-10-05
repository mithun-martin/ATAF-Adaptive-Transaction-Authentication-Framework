import { FormEvent, useEffect, useState } from "react";
import { formatINR, getProfile, updateSecurityPin, type UserProfile } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // PIN Management
  const [showPinModal, setShowPinModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPin, setNewPin] = useState("");
  const [pinLoading, setPinLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    getProfile(token)
      .then(setProfile)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load profile"));
  }, [token]);

  async function onSavePin(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    if (newPin.length < 4) {
      setError("PIN must be at least 4 digits.");
      return;
    }

    setPinLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await updateSecurityPin(token, currentPassword, newPin);
      setSuccess(res.message);
      setShowPinModal(false);
      setCurrentPassword("");
      setNewPin("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update PIN");
    } finally {
      setPinLoading(false);
    }
  }

  if (error && !profile) {
    return <p className="text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>;
  }

  if (!profile) {
    return <p className="text-gray-500">Loading profile...</p>;
  }

  const fields = [
    { label: "Full Name", value: profile.name },
    { label: "Email", value: profile.email },
    { label: "Phone", value: profile.masked_phone },
    { label: "Account Number", value: profile.account_number },
    { label: "IFSC Code", value: profile.ifsc_code },
    { label: "Balance", value: formatINR(profile.balance) },
    {
      label: "Account Created",
      value: new Date(profile.created_at).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      }),
    },
  ];

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">My Profile & Security</h1>
        <p className="text-sm text-gray-500 mt-1">Your account and Static 3FA credentials</p>
      </div>

      {success && <p className="text-sm text-green-700 bg-green-50 p-3 rounded-lg border border-green-200">{success}</p>}
      {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">{error}</p>}

      {/* Profile Card */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <div className="bg-gradient-to-r from-purple-800 to-purple-950 text-white p-6">
          <div className="w-16 h-16 bg-purple-700 rounded-full flex items-center justify-center text-2xl font-bold mb-3 shadow-inner">
            {profile.name.charAt(0).toUpperCase()}
          </div>
          <h2 className="text-xl font-bold">{profile.name}</h2>
          <p className="text-purple-200 text-sm">{profile.email}</p>
        </div>

        <div className="divide-y divide-gray-100">
          {fields.map((f) => (
            <div key={f.label} className="flex justify-between items-center px-6 py-4">
              <span className="text-gray-500 text-sm">{f.label}</span>
              <span className="font-medium text-gray-900">{f.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Static 3FA Security Settings */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <span>🛡️</span>
              <span>Factor 3: Transaction Security PIN</span>
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Used to authorize and sign the Additional Confirmation stage for every transfer. Default PIN is{" "}
              <strong className="text-purple-700">1234</strong>.
            </p>
          </div>
          <button
            onClick={() => setShowPinModal(!showPinModal)}
            className="bg-purple-700 hover:bg-purple-800 text-white text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
          >
            {showPinModal ? "Close" : "Change PIN"}
          </button>
        </div>

        {showPinModal && (
          <form onSubmit={onSavePin} className="bg-purple-50 p-4 rounded-xl border border-purple-200 space-y-3 mt-3">
            <h3 className="text-sm font-bold text-purple-900">Update Security PIN</h3>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Current Account Password</label>
              <input
                type="password"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white outline-none focus:ring-2 focus:ring-purple-500"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter account password"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">New 4-digit Security PIN</label>
              <input
                type="password"
                inputMode="numeric"
                maxLength={6}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white font-mono tracking-widest outline-none focus:ring-2 focus:ring-purple-500"
                value={newPin}
                onChange={(e) => setNewPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="••••"
                required
              />
            </div>
            <button
              type="submit"
              disabled={pinLoading || newPin.length < 4 || !currentPassword}
              className="bg-purple-700 hover:bg-purple-800 text-white px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50"
            >
              {pinLoading ? "Saving..." : "Save New PIN"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
