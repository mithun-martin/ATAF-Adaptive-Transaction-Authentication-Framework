# ATAF — Step 8: Implement Transaction-Bound Verification

## Overview

**Step 8** of the **Adaptive Transaction Authentication Framework (ATAF)** implements the **Transaction-Bound Verification Mechanism** for high-risk financial transactions.

When a transaction is flagged as **HIGH RISK** by the AI Risk Engine and Adaptive Security Policy (Steps 5, 6 & 7), standard OTP is insufficient because attackers can manipulate victims over the phone into relaying out-of-band codes. Step 8 implements **Dynamic Linking / Transaction-Bound Cryptography**, ensuring that approval corresponds strictly and immutably to the exact transaction parameters.

### Project Domain & Responsibility
* **Domain:** Cybersecurity + Cryptography
* **Responsible:** Aditya
* **Input:** High-risk transaction (from Step 7 Adaptive Policy Engine).
* **Goal:** Ensure that approval corresponds to the exact transaction being authorized.
* **Output:** Working, mathematically verified **Transaction-Bound Verification Mechanism**.

---

## Cybersecurity Threat Model & Standards Compliance

Step 8 complies with international electronic payment security standards:
* **PSD2 Regulatory Technical Standards (RTS) Article 97:** Mandates *dynamic linking* where the authentication code is cryptographically specific to the amount and payee.
* **NIST SP 800-63B (Section 5.1.4):** Requires cryptographic verifier assertions bound to the transaction context.

### Defeated Attack Vectors:
1. **Adversary-in-the-Middle (AiTM) / Amount Alteration:**
   * An attacker intercepting a transfer session attempts to change the amount (e.g., from ₹8,500 to ₹85,000). The cryptographic seal mismatch immediately aborts the transaction.
2. **Account Redirection Attack (Mule Substitution):**
   * Malware or a proxy swaps the recipient account to an attacker-controlled account. Because the destination account is hashed into the canonical payload, verification fails.
3. **Coercive Social Engineering / Vishing:**
   * Victims are presented with explicit, unmissable verification prompts (*"Did you personally initiate this transaction?"*) and anti-coercion affirmations before signing with a distinct 4-digit **Transaction Security PIN**.
4. **Replay Attacks:**
   * Ephemeral single-use cryptographic nonces ensure that intercepted authorization packets cannot be replayed.

---

## Cryptographic Protocol Specification

### 1. Canonical Serialization
Critical parameters are normalized into an unambiguous pipe-delimited canonical byte sequence:
$$\text{Canonical} = \text{challenge\_id} \mathbin{\Vert} \text{sender\_account} \mathbin{\Vert} \text{beneficiary\_account} \mathbin{\Vert} \text{amount}_{.02f} \mathbin{\Vert} \text{currency} \mathbin{\Vert} \text{timestamp} \mathbin{\Vert} \text{nonce}$$

### 2. HMAC-SHA256 Transaction Seal
$$\text{Seal} = \text{HMAC-SHA256}(K_{\text{system}}, \text{Canonical})$$

### 3. Non-Repudiation Receipt
Upon valid affirmation and Security PIN authentication, an immutable receipt hash is signed:
$$\text{Receipt} = \text{HMAC-SHA256}(K_{\text{system}}, \text{"RECEIPT"} \mathbin{\Vert} \text{challenge\_id} \mathbin{\Vert} \text{Seal} \mathbin{\Vert} \text{user\_id} \mathbin{\Vert} \text{timestamp})$$

---

## Visual Verification Challenge (ATAF Specification)

Matching the exact layout from **PDF Page 7**:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⚠️  HIGH-RISK TRANSACTION VERIFICATION CHALLENGE                            │
├──────────────────────────────────────────────────────────────────────────────┤
│  Amount            : ₹85,000.00                                              │
│  Destination       : Account XXXXXXXX4821 (Axis Bank)                        │
│  HMAC-SHA256 Seal  : 30ee84e3cd0fbb162f8336fdd6e8bc7153c6...                 │
│  Challenge Nonce   : 40bf8429fe180e147e9ea2c7057448db                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  PROMPT            : "Did you personally initiate this transaction?"         │
│  [x] Affirmation 1 : I verify that I personally initiated this transfer...   │
│  [x] Affirmation 2 : I confirm that I am not following caller instructions...│
│  Security PIN      : [ • • • • ]                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Contents

* [`crypto_engine.py`](./crypto_engine.py): HMAC-SHA256 parameter binding, constant-time verification, and replay protection.
* [`models.py`](./models.py): Pydantic contracts for challenges, explicit affirmations, and certificates.
* [`verification_service.py`](./verification_service.py): Challenge lifecycle manager, masking utilities, and authorization logic.
* [`test_transaction_binding.py`](./test_transaction_binding.py): Pytest suite testing valid flows, amount tampering, account redirection, missing affirmations, bad PIN, and replays.
* [`demo_transaction_binding.py`](./demo_transaction_binding.py): Interactive demonstration showcasing challenge issuance, valid approval, and live attack mitigations.

---

## How to Run & Verify Step 8

### 1. Run Unit Tests (100% Passing)
```fish
cd Step8
source .venv/bin/activate.fish
pytest -v test_transaction_binding.py
```
*(Tests 8 critical security assertions: normal approval, amount tampering, account redirection, missing checkboxes, wrong PIN, nonce replay, and expired challenges).*

### 2. Run Interactive Demonstration
```fish
cd Step8
source .venv/bin/activate.fish
python demo_transaction_binding.py
```

---

## Next Steps (Downstream Integration)

* **Step 9 — Integrate the Proposed System (All):**
  Integrate the Simulated Bank ([Step 1](../Step1)), the Adaptive Security Policy ([Step 7](../Step7)), and the Transaction-Bound Verification Mechanism ([Step 8](../Step8)) into the unified **Proposed Adaptive Authentication System (System 3)**.
