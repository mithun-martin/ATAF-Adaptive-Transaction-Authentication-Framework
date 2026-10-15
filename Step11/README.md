# ATAF — Step 11: Run Experimental Comparison

## Overview

**Step 11** of the **Adaptive Transaction Authentication Framework (ATAF)** delivers the comprehensive empirical benchmarking across all three authentication systems:
1. **System 1 (Baseline):** $\text{Password} \to \text{OTP} \to \text{Transaction}$ ([Step 2](../Step2))
2. **System 2 (Static 3FA):** $\text{Password} \to \text{OTP} \to \text{Additional Confirmation} \to \text{Transaction}$ ([Step 3](../Step3))
3. **System 3 (Proposed Adaptive System):** $\text{Password} \to \text{AI Risk Engine} \to \text{Adaptive Policy} \to \text{Dynamic Step-Up}$ ([Step 9](../Step9))

### Project Domain & Responsibility
* **Domain:** AI + Cybersecurity
* **Responsible:** All
* **Inputs:**
  - System 1 (Baseline), System 2 (Static 3FA), System 3 (Proposed Adaptive System)
  - IEEE-CIS Fraud Detection Test Dataset (88,581 samples from [Step 4](../Step4))
  - Trained XGBoost Classifier model from [Step 5](../Step5) / [Step 6](../Step6)
  - Standardized Social-Engineering Attack Scenarios from [Step 10](../Step10)
* **Goal:** Statistically evaluate the security vs. usability trade-offs across all three paradigms.
* **Output:** Empirical comparison tables, metrics JSON/CSV datasets, and 4 publication-grade figures.

---

## Experimental Benchmark Results

### Table 1: Security & Fraud Resilience Benchmark

| Security Metric | System 1 (Baseline 2FA) | System 2 (Static 3FA) | System 3 (Proposed Adaptive) | Optimal Target |
|---|:---:|:---:|:---:|:---:|
| **Attack Success Rate (ASR) on Social Engineering** | **100.0%** ❌ | **0.0%** ✅ | **0.0%** ✅ | $0.0\%$ (Lower is better) |
| **Fraud Detection Rate (FDR) on Social Engineering** | **0.0%** ❌ | **100.0%** ✅ | **100.0%** ✅ | $100.0\%$ (Higher is better) |
| **Large-Scale ROC-AUC Score (IEEE-CIS)** | 0.5000 | 0.5000 | **0.9468** 🏆 | $1.0000$ (Higher is better) |
| **Large-Scale PR-AUC Score (IEEE-CIS)** | 0.0350 | 0.0350 | **0.6926** 🏆 | $1.0000$ (Higher is better) |
| **False Acceptance Rate (FAR)** | 1.0000 | **0.0000** | **0.0929** | $0.0000$ (Lower is better) |
| **False Rejection / Alarm Rate (FRR)** | **0.0000** | 1.0000 ❌ | **0.1799** | $0.0000$ (Lower is better) |

---

### Table 2: Usability & Authentication Burden Benchmark

| Usability & Friction Metric | System 1 (Baseline 2FA) | System 2 (Static 3FA) | System 3 (Proposed Adaptive) | Usability Impact |
|---|:---:|:---:|:---:|---|
| **Mean Authentication Steps** | 2.00 steps | 3.00 steps | **2.05 steps** | Minimal step inflation (+2.5%) |
| **Mean Transaction Time (HCI Model)** | 17.0 s | 32.2 s | **18.1 s** | **Saves ~14.1s per transfer** vs Static 3FA |
| **Percentage Requiring Step-Up 3FA** | 0.0% | 100.0% ❌ | **4.78%** ✅ | 3FA friction confined to $<5\%$ of traffic |
| **Friction Delay vs Baseline** | 0.0% | +89.4% (Severe) | **+6.6% (Negligible)** | Near-zero perceived friction penalty |

---

## Publication Figures

The benchmark engine generates 4 high-resolution plots in `results/`:

1. **`results/security_vs_burden.png` — Pareto Security-Usability Frontier:**
   Plots Fraud Detection Rate vs. Mean Transaction Authentication Time. Demonstrates that System 3 occupies the optimal Pareto frontier, achieving maximum security (100% defense) without the 32.2s latency penalty of System 2.

2. **`results/metrics_comparison_barchart.png` — Multi-Dimensional Bar Chart:**
   Side-by-side comparison across Social-Engineering Defense, ROC-AUC, PR-AUC, FAR, and normalized Completion Time.

3. **`results/attack_defense_comparison.png` — Attack Pattern Defense Breakdown:**
   Evaluates each specific attack scenario (OTP Vishing, New Beneficiary Mule, AnyDesk Remote Takeover, Off-Hours Coercion, Volume Anomaly, and Multi-Indicator Bot Attack).

4. **`results/friction_tradeoff_curve.png` — Adaptive Policy Sensitivity Curve:**
   Plots Fraud Detection Recall vs. Benign User Step-Up Friction as the threshold $\tau_2$ sweeps from 0.10 to 0.90, highlighting the optimality of the calibrated operating point at $\tau_2 = 0.70$.

---

## Core Research Conclusions (IEEE Paper Findings)

1. **The Fallacy of Out-of-Band 2FA (System 1):**
   SMS and mobile app OTPs fail unconditionally against human-centric social engineering. Because victims are deceived into typing or reading their OTPs to attackers, System 1 exhibits a **100.0% Attack Success Rate (ASR)**.

2. **The Usability Trap of Static 3FA (System 2):**
   While demanding transaction-bound confirmation on every payment prevents attacks, it increases average completion time by **+89.4%** (from 17.0s to 32.2s) and subjects 100% of benign users to repetitive authentication fatigue, inevitably leading to habituation and blind approvals.

3. **Pareto Optimality of the Proposed Adaptive System (System 3):**
   By leveraging the calibrated XGBoost AI model alongside contextual behavioral rules:
   - System 3 achieves **100.0% defense against social engineering**, matching System 2.
   - Restricts high-friction Step-Up 3FA to only **4.78%** of total transactions.
   - Delivers a **93.4% reduction in redundant friction** compared to Static 3FA, saving genuine banking users over 14 seconds per routine transfer.

---

## How to Run Step 11

### 1. Setup Environment
```bash
cd Step11

# Create virtual environment:
uv venv --python 3.12

# Activate environment:
source .venv/bin/activate         # Bash / Zsh
source .venv/bin/activate.fish    # Fish shell

# Install dependencies:
uv pip install -r requirements.txt
```

### 2. Run Terminal Benchmark Comparison
```bash
python demo_comparison.py
```

### 3. Re-Generate Plots
```bash
python generate_plots.py
```

### 4. Run Pytest Suite
```bash
pytest test_experimental_comparison.py -v
```

---

## File Structure

```
Step11/
├── results/
│   ├── comparative_metrics.json       # Structured benchmark results dataset
│   ├── comparative_metrics.csv        # Tabular metric comparison
│   ├── attack_benchmark_results.csv   # Per-scenario breakdown table
│   ├── security_vs_burden.png         # Pareto frontier plot
│   ├── metrics_comparison_barchart.png# Multi-dimensional grouped bar chart
│   ├── attack_defense_comparison.png  # Scenario-by-scenario defense breakdown
│   └── friction_tradeoff_curve.png    # Sensitivity threshold trade-off curve
├── benchmark_runner.py                # Core experimental evaluation engine
├── generate_plots.py                  # Matplotlib / Seaborn publication plot generator
├── demo_comparison.py                 # Formatted terminal comparison runner
├── test_experimental_comparison.py    # Automated test suite (3/3 passed)
├── requirements.txt                   # Benchmark Python dependencies
└── README.md                          # Research analysis and experimental report
```
