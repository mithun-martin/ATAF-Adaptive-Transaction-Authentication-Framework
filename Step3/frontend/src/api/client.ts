const API_BASE = "http://127.0.0.1:8000";

// ─── Types ──────────────────────────────────────────

export type Account = {
  account_number: string;
  ifsc_code: string;
  balance: number;
  user_name: string;
  user_phone: string;
  masked_phone: string;
};

export type UserProfile = {
  id: number;
  name: string;
  email: string;
  phone: string;
  masked_phone: string;
  account_number: string;
  ifsc_code: string;
  balance: number;
  has_transaction_pin: boolean;
  created_at: string;
};

export type Beneficiary = {
  id: number;
  name: string;
  account_number: string;
  ifsc_code: string;
  bank_name: string;
  nickname?: string;
  created_at: string;
  masked_account?: string;
};

export type Transaction = {
  id: number;
  reference_id: string;
  beneficiary_name: string;
  beneficiary_account: string;
  amount: number;
  remark?: string;
  status: string;
  failure_reason?: string;
  auth_mode?: string;
  auth_factors?: string;
  cryptographic_seal?: string;
  created_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  message: string;
  requires_otp: boolean;
  otp_display?: string;
};

export type OTPResponse = {
  message: string;
  otp_display: string;
  expires_in: number;
};

export type TransactionChallengeResponse = {
  challenge_id: string;
  stage: string;
  message: string;
  otp_display: string;
  expires_in: number;
  amount: number;
  beneficiary_name: string;
  beneficiary_account: string;
  masked_phone: string;
};

export type TransactionAdditionalVerificationStageResponse = {
  challenge_id: string;
  stage: string;
  message: string;
  cryptographic_seal: string;
  nonce: string;
  amount: number;
  beneficiary_name: string;
  beneficiary_account: string;
  bank_name: string;
  ifsc_code: string;
  remark?: string;
  prompt: string;
};

// ─── Helpers ──────────────────────────────────────────

function authHeaders(token: string | null): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = "Request failed";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

// ─── Auth ──────────────────────────────────────────

export async function register(
  name: string,
  email: string,
  phone: string,
  password: string,
  transaction_pin: string = "1234",
) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: authHeaders(null),
    body: JSON.stringify({ name, email, phone, password, transaction_pin }),
  });
  return handleResponse(res);
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: authHeaders(null),
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<LoginResponse>(res);
}

// ─── OTP (Login) ───────────────────────────────────

export async function requestOTP(token: string, purpose: string = "LOGIN"): Promise<OTPResponse> {
  const res = await fetch(`${API_BASE}/auth/otp/generate`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ purpose }),
  });
  return handleResponse<OTPResponse>(res);
}

export async function verifyOTP(token: string, code: string, purpose: string = "LOGIN") {
  const res = await fetch(`${API_BASE}/auth/otp/verify`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ code, purpose }),
  });
  return handleResponse<{ message: string; verified: boolean }>(res);
}

// ─── Account & PIN ──────────────────────────────────────────

export async function getAccount(token: string) {
  const res = await fetch(`${API_BASE}/account`, {
    headers: authHeaders(token),
  });
  return handleResponse<Account>(res);
}

export async function getProfile(token: string) {
  const res = await fetch(`${API_BASE}/account/profile`, {
    headers: authHeaders(token),
  });
  return handleResponse<UserProfile>(res);
}

export async function updateSecurityPin(token: string, current_password: string, new_pin: string) {
  const res = await fetch(`${API_BASE}/account/pin`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ current_password, new_pin }),
  });
  return handleResponse<{ message: string }>(res);
}

// ─── Beneficiaries ──────────────────────────────────────────

export async function getBeneficiaries(token: string) {
  const res = await fetch(`${API_BASE}/beneficiaries`, {
    headers: authHeaders(token),
  });
  return handleResponse<Beneficiary[]>(res);
}

export async function addBeneficiary(
  token: string,
  data: { name: string; account_number: string; ifsc_code: string; bank_name: string; nickname?: string },
) {
  const res = await fetch(`${API_BASE}/beneficiaries`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  return handleResponse<Beneficiary>(res);
}

export async function deleteBeneficiary(token: string, id: number) {
  const res = await fetch(`${API_BASE}/beneficiaries/${id}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  return handleResponse<void>(res);
}

// ─── Transactions (Static 3FA) ──────────────────────────

export async function getTransactions(token: string) {
  const res = await fetch(`${API_BASE}/transactions`, {
    headers: authHeaders(token),
  });
  return handleResponse<Transaction[]>(res);
}

// Factor 1: Password
export async function initiateTransaction(
  token: string,
  data: { beneficiary_id: number; amount: number; remark?: string; password: string },
): Promise<TransactionChallengeResponse> {
  const res = await fetch(`${API_BASE}/transactions/initiate`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  return handleResponse<TransactionChallengeResponse>(res);
}

// Factor 2: OTP
export async function verifyTransactionOTP(
  token: string,
  challenge_id: string,
  otp_code: string,
): Promise<TransactionAdditionalVerificationStageResponse> {
  const res = await fetch(`${API_BASE}/transactions/verify-otp`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ challenge_id, otp_code }),
  });
  return handleResponse<TransactionAdditionalVerificationStageResponse>(res);
}

// Factor 3: Additional Confirmation (Transaction-Bound Verification)
export async function confirmAdditionalVerification(
  token: string,
  data: {
    challenge_id: string;
    transaction_pin: string;
    explicit_confirmation: boolean;
    anti_coercion_confirmation: boolean;
  },
): Promise<Transaction> {
  const res = await fetch(`${API_BASE}/transactions/confirm-additional-verification`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
  return handleResponse<Transaction>(res);
}

export async function resendTransactionOTP(
  token: string,
  challenge_id: string,
): Promise<TransactionChallengeResponse> {
  const res = await fetch(`${API_BASE}/transactions/resend-otp`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ challenge_id }),
  });
  return handleResponse<TransactionChallengeResponse>(res);
}

export async function cancelTransaction(token: string, challenge_id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/transactions/cancel`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ challenge_id }),
  });
  return handleResponse<void>(res);
}

// ─── Formatting ──────────────────────────────────────────

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}
