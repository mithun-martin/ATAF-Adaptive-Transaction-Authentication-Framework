# ATAF — Step 7: Design the Adaptive Security Policy

## Overview

**Step 7** of the **Adaptive Transaction Authentication Framework (ATAF)** designs and implements the **Adaptive Security Policy Engine**.

This policy bridges the **AI Transaction Risk Model** (developed in Steps 5 & 6) and the **Authentication Mechanisms** (built in Steps 2, 3 & 8). Instead of applying static authentication regardless of context, this policy dynamically adjusts authentication intensity based on real-time transaction risk:

$$\text{Transaction Context} \xrightarrow{\quad\text{AI Risk Model}\quad} \text{Risk Score } R \xrightarrow{\quad\text{Policy Engine}\quad} \begin{cases} \text{LOW RISK:} & \text{Normal 2FA} \\ \text{MEDIUM RISK:} & \text{Warning Banner + OTP} \\ \text{HIGH RISK:} & \text{Strong 3FA (Seal + PIN)} \end{cases}$$

### Project Domain & Responsibility
* **Domain:** AI + Cybersecurity
* **Responsible:** Mithun (AI) + Aditya (Cybersecurity)
* **Input:** AI Risk Score ($R \in [0.0, 1.0]$) output by the selected XGBoost model from Step 6.
* **Goal:** Make transaction authentication dynamically depend on transaction risk.
* **Output:** Working, tested **Adaptive Authentication Policy Engine**.

---

## Mathematical Formulation & Tri-Tier Policy Matrix

The policy decision function $D(R)$ partitions the continuous risk space $[0.0, 1.0]$ into three operational tiers using calibrated cutoffs $\tau_1$ and $\tau_2$:

$$D(R) = \begin{cases} \text{LOW RISK (Normal 2FA)}, & \text{if } R < \tau_1 \\ \text{MEDIUM RISK (Warning + OTP)}, & \text{if } \tau_1 \le R < \tau_2 \\ \text{HIGH RISK (Strong Verification 3FA)}, & \text{if } R \ge \tau_2 \end{cases}$$

| Risk Tier | Risk Score Range ($R$) | Enforced Authentication Policy | Factors Required | Security Mechanism & User Experience |
|---|---|---|---|---|
| **🟢 LOW RISK** | $R < 0.30$ | **Normal 2FA** | Password + OTP | Routine, low-friction transfers. Eliminates user fatigue on legitimate daily payments. |
| **🟡 MEDIUM RISK** | $0.30 \le R < 0.70$ | **Advisory Warning + OTP** | Password + OTP | Displays prominent **Anti-Social-Engineering Warning Banner** explaining specific risk flags before OTP entry. |
| **🔴 HIGH RISK** | $R \ge 0.70$ | **Strong Verification (3FA)** | Password + OTP + Additional Confirmation | Mandates transaction-bound cryptographic seal (HMAC-SHA256) and 4-digit **Transaction Security PIN**. |

---

## Threshold Calibration Rationale (Step 6 Ingestion)

Based on the test evaluation curves produced in Step 6 (`Step6/outputs/threshold_analysis.png` and `metrics_table.csv` on 88,581 IEEE-CIS transactions):

* **$\tau_1 = 0.30$ (Low $\to$ Medium):**
  * Routine transactions ($R < 0.30$) represent the vast majority of legitimate user banking activities.
  * Setting $\tau_1 = 0.30$ keeps false positive friction at a minimum for day-to-day transfers.
* **$\tau_2 = 0.70$ (Medium $\to$ High):**
  * Transactions with $R \ge 0.70$ exhibit extreme anomaly scores or multiple concurring fraud indicators (unusual amount ratio $\ge 10\times$, night-time execution, new recipient).
  * High-risk escalation mandates explicit transaction binding and a separate security PIN, neutralizing vishing and unauthorized transfer attempts.

---

## Cybersecurity Design Principles

1. **Anti-Coercion / Social-Engineering Disruption:**
   * In medium-risk scenarios, the warning banner interrupts psychological manipulation (e.g., urgent scam callers ordering victims to read out OTPs) by explicitly warning: *"If you were instructed to transfer this amount over a call, this may be an impersonation scam."*
2. **Transaction-Bound Cryptographic Binding:**
   * High-risk transactions require the HMAC-SHA256 seal and Security PIN established in Step 3, ensuring mathematical non-repudiation and recipient lock-in.
3. **Fail-Secure Architecture:**
   * If the AI inference engine or feature pipeline encounters any failure, timeout, or missing data, the policy engine safely **defaults to HIGH RISK (Strong Verification)** rather than permitting an uninspected low-friction transfer.

---

## Directory Contents

* [`threshold_config.py`](./threshold_config.py): Configurable thresholds ($\tau_1, \tau_2$), risk tiers, and rule weights.
* [`scorer.py`](./scorer.py): Loads the trained XGBoost model from `Step5/models/xgboost.pkl` and provides feature anomaly scoring.
* [`policy_engine.py`](./policy_engine.py): Core `AdaptivePolicyEngine` executing the decision matrix and fail-secure logic.
* [`test_policy_engine.py`](./test_policy_engine.py): Pytest suite covering all 3 tiers, boundary conditions, and fail-secure recovery.
* [`demo_policy.py`](./demo_policy.py): Interactive demonstration evaluating 5 realistic banking transaction scenarios.

---

## How to Run & Test Step 7

### 1. Run Unit Test Suite
```bash
cd Step7
uv run --with pytest --with pydantic --with joblib --with numpy --with scikit-learn pytest -v test_policy_engine.py
```
*(All 8 unit tests pass covering low, medium, high, boundary conditions, and fail-secure triggers).*

### 2. Run Interactive Scenario Demo
```bash
cd Step7
uv run --with pydantic --with joblib --with numpy python demo_policy.py
```
Simulates 5 real-world scenarios:
1. Routine Grocery Transfer ($\to$ 🟢 LOW RISK)
2. Moderate Rent Payment ($\to$ 🟢 LOW RISK)
3. Unfamiliar New Recipient ($\to$ 🟡 MEDIUM RISK + Warning Banner)
4. High-Velocity Spike ($\to$ 🔴 HIGH RISK + Strong Verification 3FA)
5. Urgent Social Engineering Scam ($\to$ 🔴 HIGH RISK + Strong Verification 3FA)

---

## Downstream Integration (Step 8 & Step 9)

* **Step 8:** Consumes the `STRONG_VERIFICATION` directive to render the cryptographic HMAC-SHA256 transaction-bound verification modal.
* **Step 9:** Integrates this engine directly into the live backend transaction route (`/transactions/initiate` $\to$ `/transactions/evaluate-policy`).
