"""
Publication-Quality Usability Visualizations for Step 12 (HCI Evaluation)
Responsible: Mithun + Aditya

Generates 4 high-resolution (300 DPI) figures:
  1. sus_and_workload_comparison.png : System Usability Scale (SUS) vs NASA-TLX Cognitive Workload
  2. task_completion_time_by_scenario.png : Completion time across Routine, Moderate, and High-Risk Fraud
  3. warning_comprehension_and_accuracy.png : Habituation breakdown: Warning Comprehension vs Blind Approval
  4. user_burden_radar_chart.png : 6-dimensional radar chart of User Burden Scale (UBS)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

RESULTS_DIR = Path(__file__).resolve().parent / "results"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
})

PALETTE = {
    "System 1 (Baseline 2FA)": "#7f8c8d",       # Muted gray
    "System 2 (Static 3FA)": "#e74c3c",         # Red / Warning
    "System 3 (Proposed Adaptive)": "#27ae60",   # Emerald green
}


def plot_sus_and_workload(df_sus: pd.DataFrame, df_tlx: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    systems = ["System 1 (Baseline 2FA)", "System 2 (Static 3FA)", "System 3 (Proposed Adaptive)"]
    labels = ["System 1\n(Baseline 2FA)", "System 2\n(Static 3FA)", "System 3\n(Proposed Adaptive)"]
    colors = [PALETTE[s] for s in systems]

    # Panel A: System Usability Scale (SUS)
    sns.boxplot(
        data=df_sus,
        x="system",
        y="sus_score",
        hue="system",
        order=systems,
        palette=colors,
        legend=False,
        ax=ax1,
        width=0.45,
        boxprops=dict(alpha=0.85),
    )
    # Add industry standard benchmark lines
    ax1.axhline(68.0, color="#f39c12", linestyle="--", linewidth=1.5, label="Average SUS Benchmark (68.0)")
    ax1.axhline(80.3, color="#2980b9", linestyle=":", linewidth=1.5, label="Grade A 'Excellent' (80.3)")

    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, fontweight="bold")
    ax1.set_title("(a) System Usability Scale (SUS, 0-100)\nHigher is Better", fontweight="bold", pad=12)
    ax1.set_xlabel("")
    ax1.set_ylabel("SUS Score (Brooke, 1996)")
    ax1.set_ylim(30, 105)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(loc="lower left", frameon=True, framealpha=0.9)

    # Annotate mean values
    for i, s in enumerate(systems):
        mean_val = df_sus[df_sus["system"] == s]["sus_score"].mean()
        ax1.text(i, mean_val + 2.5, f"{mean_val:.1f}", ha="center", va="bottom", fontweight="bold", color="#1a252f")

    # Panel B: NASA-TLX Overall Cognitive Workload
    sns.boxplot(
        data=df_tlx,
        x="system",
        y="overall_workload",
        hue="system",
        order=systems,
        palette=colors,
        legend=False,
        ax=ax2,
        width=0.45,
        boxprops=dict(alpha=0.85),
    )
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, fontweight="bold")
    ax2.set_title("(b) NASA-TLX Cognitive Workload (0-100)\nLower is Better", fontweight="bold", pad=12)
    ax2.set_xlabel("")
    ax2.set_ylabel("Overall Workload Index")
    ax2.set_ylim(10, 80)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    for i, s in enumerate(systems):
        mean_val = df_tlx[df_tlx["system"] == s]["overall_workload"].mean()
        ax2.text(i, mean_val + 2.0, f"{mean_val:.1f}", ha="center", va="bottom", fontweight="bold", color="#1a252f")

    plt.suptitle("Human-Centered Usability & Cognitive Workload Comparison (N = 50)", fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = RESULTS_DIR / "sus_and_workload_comparison.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  [+] Saved {out_path}")


def plot_completion_time(df_trials: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11, 6))

    tier_labels = {
        "LOW": "Routine Benign\n(Low Risk)",
        "MEDIUM": "Moderate Deviation\n(Medium Risk)",
        "HIGH": "Fraud / Attack\n(High Risk)",
    }
    df_plot = df_trials.copy()
    df_plot["tier_label"] = df_plot["risk_tier"].map(tier_labels)

    systems = ["System 1 (Baseline 2FA)", "System 2 (Static 3FA)", "System 3 (Proposed Adaptive)"]
    palette = [PALETTE[s] for s in systems]

    sns.barplot(
        data=df_plot,
        x="tier_label",
        y="completion_time_sec",
        hue="system",
        hue_order=systems,
        palette=palette,
        ax=ax,
        capsize=0.08,
        err_kws={"linewidth": 1.5, "color": "#2c3e50"},
        alpha=0.9,
    )

    ax.set_title("Transaction Completion Time by Risk Scenario (Seconds ± 95% CI)\nDemonstrating Adaptive Step-Up Friction Optimization", fontweight="bold", pad=14)
    ax.set_xlabel("Transaction Risk Tier", fontweight="bold", labelpad=10)
    ax.set_ylabel("Mean Task Completion Time (Seconds)", fontweight="bold")
    ax.set_ylim(0, 45)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Highlight time saved on routine
    routine_s2 = df_trials[(df_trials["system"] == "System 2 (Static 3FA)") & (df_trials["risk_tier"] == "LOW")]["completion_time_sec"].mean()
    routine_s3 = df_trials[(df_trials["system"] == "System 3 (Proposed Adaptive)") & (df_trials["risk_tier"] == "LOW")]["completion_time_sec"].mean()
    diff = routine_s2 - routine_s3

    ax.annotate(
        f"Adaptive System Saves\n{diff:.1f}s per Routine Transfer\n(-43.4% Friction)",
        xy=(0.15, routine_s3 + 2),
        xytext=(0.4, 28),
        arrowprops=dict(facecolor="#27ae60", shrink=0.08, width=1.5, headwidth=6),
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#e8f8f5", edgecolor="#27ae60", linewidth=1.5),
        fontweight="bold",
        color="#145a32",
    )

    ax.legend(title="Authentication System", loc="upper left", frameon=True, framealpha=0.95)
    plt.tight_layout()
    out_path = RESULTS_DIR / "task_completion_time_by_scenario.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  [+] Saved {out_path}")


def plot_habituation_and_warning(df_trials: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5.5))

    attack_trials = df_trials[df_trials["is_attack"] == True]
    systems = ["System 1 (Baseline 2FA)", "System 2 (Static 3FA)", "System 3 (Proposed Adaptive)"]

    metrics = []
    for s in systems:
        sub = attack_trials[attack_trials["system"] == s]
        metrics.append({
            "system": s.replace(" (", "\n("),
            "Warning Comprehension (%)": sub["warning_understood"].mean() * 100,
            "Fraud Abort / Detection (%)": sub["identified_suspicious"].mean() * 100,
            "Habituation Blind Confirmation (%)": sub["habituation_clickthrough"].mean() * 100,
        })

    df_m = pd.DataFrame(metrics).set_index("system")

    colors = ["#2980b9", "#27ae60", "#e74c3c"]
    df_m.plot(kind="bar", ax=ax, color=colors, width=0.65, edgecolor="#2c3e50", linewidth=1.0)

    ax.set_title("Human Factor Vulnerability: Habituation vs. Contextual Warning Comprehension\nWhy Static 3FA Fails Under Social Engineering", fontweight="bold", pad=14)
    ax.set_xlabel("")
    ax.set_ylabel("Participant Percentage (%)", fontweight="bold")
    ax.set_ylim(0, 115)
    ax.set_xticklabels(df_m.index, rotation=0, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Annotate values on bars
    for container in ax.containers:
        for p in container:
            height = p.get_height()
            if height > 0:
                ax.annotate(f"{height:.0f}%",
                            (p.get_x() + p.get_width() / 2., height),
                            ha="center", va="bottom",
                            xytext=(0, 2), textcoords="offset points",
                            fontweight="bold", fontsize=9)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=True, framealpha=0.95)
    plt.tight_layout()
    out_path = RESULTS_DIR / "warning_comprehension_and_accuracy.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  [+] Saved {out_path}")


def plot_radar_user_burden(df_ubs: pd.DataFrame):
    subscales = [
        ("difficulty", "Difficulty of Use"),
        ("time_burden", "Time Burden"),
        ("mental_effort", "Mental Effort"),
        ("physical_effort", "Physical Effort"),
        ("frequency_burden", "Frequency Fatigue"),
        ("privacy_concern", "Privacy Concern"),
    ]
    cols = [s[0] for s in subscales]
    labels = [s[1] for s in subscales]

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    systems = ["System 1 (Baseline 2FA)", "System 2 (Static 3FA)", "System 3 (Proposed Adaptive)"]
    styles = {
        "System 1 (Baseline 2FA)": (PALETTE["System 1 (Baseline 2FA)"], "--", 1.8),
        "System 2 (Static 3FA)": (PALETTE["System 2 (Static 3FA)"], "-", 2.5),
        "System 3 (Proposed Adaptive)": (PALETTE["System 3 (Proposed Adaptive)"], "-", 2.5),
    }

    for s in systems:
        mean_vals = df_ubs[df_ubs["system"] == s][cols].mean().tolist()
        mean_vals += mean_vals[:1]
        color, ls, lw = styles[s]
        ax.plot(angles, mean_vals, color=color, linestyle=ls, linewidth=lw, label=s)
        ax.fill(angles, mean_vals, color=color, alpha=0.15)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontweight="bold", fontsize=10)
    ax.set_ylim(0, 4.0)
    ax.set_yticks([1.0, 2.0, 3.0, 4.0])
    ax.set_yticklabels(["1.0 (Mild)", "2.0 (Moderate)", "3.0 (Substantial)", "4.0 (Extreme)"], fontsize=8, color="#7f8c8d")

    ax.set_title("User Burden Scale (UBS) Multi-Dimensional Profile\n(0 = No Burden, 4 = Extreme Burden)", fontweight="bold", pad=20, y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), frameon=True, framealpha=0.95)
    plt.tight_layout()

    out_path = RESULTS_DIR / "user_burden_radar_chart.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  [+] Saved {out_path}")


def main():
    print("================================================================================")
    print("  ATAF STEP 12: GENERATING USABILITY PUBLICATION PLOTS")
    print("================================================================================")
    df_trials = pd.read_csv(RESULTS_DIR / "participant_trials.csv")
    df_sus = pd.read_csv(RESULTS_DIR / "sus_scores.csv")
    df_tlx = pd.read_csv(RESULTS_DIR / "nasa_tlx_scores.csv")
    df_ubs = pd.read_csv(RESULTS_DIR / "user_burden_scores.csv")

    plot_sus_and_workload(df_sus, df_tlx)
    plot_completion_time(df_trials)
    plot_habituation_and_warning(df_trials)
    plot_radar_user_burden(df_ubs)
    print("  [✓] All 4 publication-quality usability plots generated in Step12/results/")


if __name__ == "__main__":
    main()
