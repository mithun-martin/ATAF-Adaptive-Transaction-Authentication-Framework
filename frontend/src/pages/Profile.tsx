import { useEffect, useState } from "react";
import { formatINR, getProfile, type UserProfile } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    getProfile(token)
      .then(setProfile)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load profile"));
  }, [token]);

  if (error) {
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
    { label: "Account Created", value: new Date(profile.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" }) },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Profile</h1>
        <p className="text-sm text-gray-500 mt-1">Your account details</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="bg-gradient-to-r from-blue-800 to-blue-950 text-white p-6">
          <div className="w-16 h-16 bg-blue-700 rounded-full flex items-center justify-center text-2xl font-bold mb-3">
            {profile.name.charAt(0).toUpperCase()}
          </div>
          <h2 className="text-xl font-bold">{profile.name}</h2>
          <p className="text-blue-200 text-sm">{profile.email}</p>
        </div>

        <div className="divide-y divide-gray-100">
          {fields.map((f) => (
            <div key={f.label} className="flex justify-between items-center px-6 py-4">
              <span className="text-gray-500 text-sm">{f.label}</span>
              <span className="font-medium">{f.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
