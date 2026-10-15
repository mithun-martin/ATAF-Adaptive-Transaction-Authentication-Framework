# ATAF — Step 10: Create Social-Engineering Attack Scenarios

## Overview

**Step 10** of the **Adaptive Transaction Authentication Framework (ATAF)** creates a standardized, reproducible **Social-Engineering Attack Scenario Set** designed to evaluate how different authentication architectures withstand modern human-centric fraud tactics.

### Project Domain & Responsibility
* **Domain:** Cybersecurity
* **Responsible:** Aditya
* **Input:** Three authentication systems:
  1. **System 1 (Baseline):** $\text{Password} \to \text{OTP} \to \text{Transaction}$ ([Step 2](../Step2))
  2. **System 2 (Static 3FA):** $\text{Password} \to \text{OTP} \to \text{Additional Confirmation} \to \text{Transaction}$ ([Step 3](../Step3))
  3. **System 3 (Proposed Adaptive):** $\text{Password} \to \text{AI Risk Engine} \to \text{Adaptive Policy} \to \text{Dynamic Step-Up}$ ([Step 9](../Step9))
* **Goal:** Create controlled, realistic scenarios to benchmark fraud resilience vs. user authentication burden.
* **Output:** Standardized Social-Engineering Attack Scenario Catalog and Multi-System Simulation Harness.

---

## Threat Model & Attack Taxonomy

Traditional banking 2FA assumes that out-of-band possession factors (SMS/App OTP) guarantee transactional intent. In modern social engineering, attackers exploit psychological vulnerabilities (fear, urgency, technical confusion, greed) to convince victims to willingly authorize fraudulent transfers or recite verification codes.

### Attack Catalog Summary

| Scenario ID | Attack Pattern | Threat Severity | Pretext Narrative | MITRE ATT&CK Mapping |
|---|---|---|---|---|
| **SCN-01** | **OTP Social Engineering** | HIGH | Attacker impersonates bank fraud department claiming an unauthorized charge is pending; tricks victim into reciting OTP to "cancel" the charge. | T1566.002 (Voice Phishing / Vishing) |
| **SCN-02** | **New Beneficiary + Large Transfer** | CRITICAL | WhatsApp impersonation scam claiming a relative was hospitalized in an emergency, demanding ₹48,000 to a freshly added mule account. | T1657 (Financial Theft via Pretexting) |
| **SCN-03** | **New Device + Large Transfer** | CRITICAL | Remote access takeover (AnyDesk/TeamViewer) under the guise of telecom 5G KYC upgrade; attacker initiates ₹65,000 transfer from a new session. | T1219 (Remote Access) & T1539 (Session Stealing) |
| **SCN-04** | **Unusual Transaction Time** | HIGH | "Digital arrest" extortion call at 02:45 AM impersonating law enforcement; coerces panic transfer of ₹35,000 during off-hours. | T1657 (Extortion & Law Enforcement Impersonation) |
| **SCN-05** | **Unusual Transaction Amount** | HIGH | Fake high-yield crypto investment advisory promising 400% returns; lures victim to transfer ₹90,000 (22.5x historical volume). | T1657 (Financial Fraud / Investment Scam) |
| **SCN-06** | **Multiple Suspicious Indicators** | CRITICAL | Compound automated takeover: credential stuffing, rapid burst transfers (3 in 30m), new beneficiary, night-time (03:00 AM), and ₹75,000 sum. | T1110 (Brute Force) & T1499 (Distraction Spam) |
| **SCN-07** | **Benign Control 1 (Grocery)** | LOW | Routine daytime payment of ₹650 to an established local merchant (usability baseline). | N/A (Legitimate User Activity) |
| **SCN-08** | **Benign Control 2 (Rent)** | LOW | Scheduled daytime payment of ₹15,000 monthly rent to an established landlord (usability baseline). | N/A (Legitimate User Activity) |

---

## Multi-System Benchmark Results

The scenario catalog was simulated across all three systems using `attack_simulator.py`:

```
================================================================================
  EXECUTIVE SUMMARY & BENCHMARK COMPARISON
================================================================================
  Total Attack Scenarios Tested     : 6
  System 1 (Baseline 2FA) Defense   : 0/6 (0.0%)   [CRITICAL VULNERABILITY]
  System 2 (Static 3FA) Defense     : 6/6 (100.0%) [HIGH DEFENSE]
  System 3 (Proposed Adaptive)      : 6/6 (100.0%) [HIGH DEFENSE]

  USABILITY & AUTHENTICATION BURDEN (Benign Control Scenarios):
  System 1 Average Friction Steps   : 2.0 steps (Password + OTP)
  System 2 Average Friction Steps   : 3.0 steps (Always 3 factors, high user fatigue)
  System 3 Average Friction Steps   : 2.0 steps (Frictionless 2FA for routine activity)
================================================================================
```

### Key Comparative Findings

1. **System 1 (Baseline 2FA) Vulnerability:**
   Fails against **100%** of social-engineering attacks because victims readily provide or enter OTPs when under false pretexts or coercion. System 1 lacks transactional context awareness.

2. **System 2 (Static 3FA) Over-Enforcement:**
   Successfully halts all 6 attacks by displaying recipient details and demanding an offline PIN, but **penalizes 100% of benign transfers** with redundant 3-factor friction, creating user fatigue.

3. **System 3 (Proposed Adaptive) Optimal Frontier:**
   Matches the **100% fraud prevention** of Static 3FA while preserving the **frictionless 2-step experience** of System 1 for legitimate transfers ($R < 0.30$), achieving the ideal security-usability balance.

---

## How to Run Step 10

### 1. Environment Setup
```bash
cd Step10

# Create virtual environment:
uv venv --python 3.12

# Activate environment:
source .venv/bin/activate         # Bash / Zsh
source .venv/bin/activate.fish    # Fish shell

# Install dependencies:
uv pip install -r requirements.txt
```

### 2. Run Interactive Terminal Benchmark Demo
```bash
python demo_attack_scenarios.py
```

### 3. Run Automated Pytest Suite
```bash
pytest test_attack_scenarios.py -v
```

---

## File Structure

```
Step10/
├── scenarios/
│   ├── __init__.py           # Package exports
│   ├── models.py             # Pydantic data schemas for attacks and outcomes
│   ├── scenarios.json        # Machine-readable scenario catalog (8 scenarios)
│   └── catalog.py            # Scenario loader, query, and filter utilities
├── attack_simulator.py       # Multi-system comparative simulation engine
├── demo_attack_scenarios.py  # Interactive terminal comparison runner
├── test_attack_scenarios.py  # Automated test suite (5/5 tests passing)
├── requirements.txt          # Minimal Python dependencies
└── README.md                 # Architecture, threat model, and benchmark documentation
```
