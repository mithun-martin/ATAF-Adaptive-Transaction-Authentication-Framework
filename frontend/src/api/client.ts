const API_BASE = "http://127.0.0.1:8000";

export type Account = {
  account_number: string;
  balance: number;
  user_name: string;
};

export type Beneficiary = {
  id: number;
  name: string;
  account_number: string;
  bank_name: string;
  created_at: string;
  masked_account?: string;
};

export type Transaction = {
  id: number;
  beneficiary_name: string;
  beneficiary_account: string;
  amount: number;
  status: string;
  created_at: string;
};

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

export async function register(name: string, email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: authHeaders(null),
    body: JSON.stringify({ name, email, password }),
  });
  return handleResponse(res);
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: authHeaders(null),
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<{ access_token: string; message: string }>(res);
}

export async function getAccount(token: string) {
  const res = await fetch(`${API_BASE}/account`, {
    headers: authHeaders(token),
  });
  return handleResponse<Account>(res);
}

export async function getBeneficiaries(token: string) {
  const res = await fetch(`${API_BASE}/beneficiaries`, {
    headers: authHeaders(token),
  });
  return handleResponse<Beneficiary[]>(res);
}

export async function addBeneficiary(
  token: string,
  name: string,
  account_number: string,
  bank_name: string,
) {
  const res = await fetch(`${API_BASE}/beneficiaries`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ name, account_number, bank_name }),
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

export async function getTransactions(token: string) {
  const res = await fetch(`${API_BASE}/transactions`, {
    headers: authHeaders(token),
  });
  return handleResponse<Transaction[]>(res);
}

export async function createTransaction(token: string, beneficiary_id: number, amount: number) {
  const res = await fetch(`${API_BASE}/transactions`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ beneficiary_id, amount }),
  });
  return handleResponse<Transaction>(res);
}

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}
