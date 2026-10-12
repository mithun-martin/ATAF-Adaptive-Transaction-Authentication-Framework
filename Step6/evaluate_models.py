"""
Step 6 -- Evaluate and Select the AI Model
===========================================
Loads all three trained models from Step 5 and evaluates them on the
held-out TEST set from Step 4 using:

  - Precision
  - Recall (True Positive Rate)
  - F1-Score
  - ROC-AUC
  - PR-AUC  (key metric for imbalanced fraud detection)
  - False Positive Rate (FPR)
  - False Negative Rate (FNR)

Generates comparison plots and declares the winning model that will be
used as the AI Risk Engine in Steps 7-9.

Usage:
    python evaluate_models.py

Outputs (in outputs/):
    metrics_table.csv            -- All metrics for all models
    roc_curves.png               -- ROC curve comparison
    pr_curves.png                -- Precision-Recall curve comparison
    confusion_matrices.png       -- Side-by-side confusion matrices
    threshold_analysis.png       -- Precision/Recall vs threshold (best model)
    evaluation_report.txt        -- Full evaluation report + model selection
    best_model.txt               -- Name of the selected model (for Step 7)
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    roc_curve, precision_recall_curve,
    confusion_matrix, classification_report,
)

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---- Config ------------------------------------------------------------------
MODELS_DIR    = "../Step5/models"
PROCESSED_DIR = "../Step4/data/processed"
OUTPUT_DIR    = "outputs"
TARGET        = "isFraud"
# Classification threshold -- tune here if needed; 0.5 is the default
THRESHOLD     = 0.5
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_FILES = {
    "Logistic Regression": "logistic_regression.pkl",
    "Random Forest":       "random_forest.pkl",
    "XGBoost":             "xgboost.pkl",
}

# ---- Load test data ----------------------------------------------------------
def load_test_data():
    print("Loading held-out test set from Step 4...")
    test = pd.read_parquet(os.path.join(PROCESSED_DIR, "test_processed.parquet"))
    X_test = test.drop(columns=[TARGET]).astype(np.float32)
    y_test = test[TARGET]
    print(f"  Test set: {X_test.shape} | Fraud rate: {y_test.mean()*100:.2f}%")
    return X_test, y_test

# ---- Load models -------------------------------------------------------------
def load_models():
    models = {}
    for name, fname in MODEL_FILES.items():
        path = os.path.join(MODELS_DIR, fname)
        print(f"  Loading {name} from {path}")
        models[name] = joblib.load(path)
    return models

# ---- Compute all metrics for one model ---------------------------------------
def evaluate_model(model, X_test, y_test, name):
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= THRESHOLD).astype(int)

    precision  = precision_score(y_test, preds, zero_division=0)
    recall     = recall_score(y_test, preds, zero_division=0)      # TPR
    f1         = f1_score(y_test, preds, zero_division=0)
    roc_auc    = roc_auc_score(y_test, probs)
    pr_auc     = average_precision_score(y_test, probs)            # AP = PR-AUC

    cm = confusion_matrix(y_test, preds)
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0                # False Positive Rate
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0                # False Negative Rate

    return {
        "Model":     name,
        "Precision": round(precision, 4),
        "Recall":    round(recall,    4),
        "F1-Score":  round(f1,        4),
        "ROC-AUC":   round(roc_auc,   4),
        "PR-AUC":    round(pr_auc,    4),
        "FPR":       round(fpr,       4),
        "FNR":       round(fnr,       4),
        "TP": int(tp), "FP": int(fp),
        "TN": int(tn), "FN": int(fn),
        "_probs": probs,
        "_cm": cm,
    }

# ---- ROC Curve Plot ----------------------------------------------------------
def plot_roc_curves(models, results, X_test, y_test):
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["steelblue", "darkorange", "green"]
    for (name, model), color in zip(models.items(), colors):
        probs = model.predict_proba(X_test)[:, 1]
        fpr_arr, tpr_arr, _ = roc_curve(y_test, probs)
        auc = next(r["ROC-AUC"] for r in results if r["Model"] == name)
        ax.plot(fpr_arr, tpr_arr, label=f"{name} (AUC={auc})", color=color, lw=2)
    ax.plot([0,1],[0,1], "k--", lw=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate (Recall)")
    ax.set_title("ROC Curves -- Model Comparison")
    ax.legend(loc="lower right")
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "roc_curves.png"), dpi=150)
    plt.close(fig)
    print("  Saved -> outputs/roc_curves.png")

# ---- PR Curve Plot -----------------------------------------------------------
def plot_pr_curves(models, results, X_test, y_test):
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["steelblue", "darkorange", "green"]
    baseline = y_test.mean()
    for (name, model), color in zip(models.items(), colors):
        probs = model.predict_proba(X_test)[:, 1]
        prec_arr, rec_arr, _ = precision_recall_curve(y_test, probs)
        pr_auc = next(r["PR-AUC"] for r in results if r["Model"] == name)
        ax.plot(rec_arr, prec_arr, label=f"{name} (AP={pr_auc})", color=color, lw=2)
    ax.axhline(baseline, color="gray", linestyle="--", lw=1, label=f"Baseline (fraud rate={baseline:.3f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curves -- Model Comparison")
    ax.legend(loc="upper right")
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "pr_curves.png"), dpi=150)
    plt.close(fig)
    print("  Saved -> outputs/pr_curves.png")

# ---- Confusion Matrices Plot -------------------------------------------------
def plot_confusion_matrices(results):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, r in zip(axes, results):
        cm = r["_cm"]
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues", ax=ax,
            xticklabels=["Predicted: Legit", "Predicted: Fraud"],
            yticklabels=["Actual: Legit", "Actual: Fraud"],
        )
        ax.set_title(f"{r['Model']}\nF1={r['F1-Score']} | PR-AUC={r['PR-AUC']}")
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "confusion_matrices.png"), dpi=150)
    plt.close(fig)
    print("  Saved -> outputs/confusion_matrices.png")

# ---- Threshold Analysis (best model only) ------------------------------------
def plot_threshold_analysis(best_model, best_name, X_test, y_test):
    probs = best_model.predict_proba(X_test)[:, 1]
    thresholds = np.linspace(0.01, 0.99, 200)
    precisions, recalls, f1s, fprs = [], [], [], []

    for t in thresholds:
        preds = (probs >= t).astype(int)
        precisions.append(precision_score(y_test, preds, zero_division=0))
        recalls.append(recall_score(y_test, preds, zero_division=0))
        f1s.append(f1_score(y_test, preds, zero_division=0))
        cm = confusion_matrix(y_test, preds)
        tn, fp, fn, tp = cm.ravel()
        fprs.append(fp / (fp + tn) if (fp + tn) > 0 else 0)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(thresholds, precisions, label="Precision",  color="steelblue", lw=2)
    ax.plot(thresholds, recalls,    label="Recall",     color="crimson",   lw=2)
    ax.plot(thresholds, f1s,        label="F1-Score",   color="green",     lw=2)
    ax.plot(thresholds, fprs,       label="FPR",        color="orange",    lw=2, linestyle="--")
    ax.axvline(THRESHOLD, color="gray", linestyle=":", lw=1.5, label=f"Default threshold={THRESHOLD}")
    ax.set_xlabel("Classification Threshold")
    ax.set_ylabel("Score")
    ax.set_title(f"Threshold Analysis -- {best_name}")
    ax.legend()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "threshold_analysis.png"), dpi=150)
    plt.close(fig)
    print("  Saved -> outputs/threshold_analysis.png")

# ---- Metrics Bar Chart -------------------------------------------------------
def plot_metrics_bar(results):
    metrics = ["Precision", "Recall", "F1-Score", "ROC-AUC", "PR-AUC"]
    df = pd.DataFrame(results)[["Model"] + metrics].set_index("Model")

    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(metrics))
    width = 0.22
    colors = ["steelblue", "darkorange", "green"]
    for i, (model_name, row) in enumerate(df.iterrows()):
        ax.bar(x + i * width, row[metrics].values, width, label=model_name, color=colors[i])

    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics)
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_title("Model Comparison -- Key Metrics")
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "metrics_comparison.png"), dpi=150)
    plt.close(fig)
    print("  Saved -> outputs/metrics_comparison.png")

# ---- Select Best Model -------------------------------------------------------
def select_best_model(results):
    """
    Primary criterion: PR-AUC (best for imbalanced fraud detection).
    Tie-breaker: F1-Score.
    """
    best = max(results, key=lambda r: (r["PR-AUC"], r["F1-Score"]))
    return best

# ---- Save full report --------------------------------------------------------
def save_report(results, best):
    df = pd.DataFrame(results)[
        ["Model", "Precision", "Recall", "F1-Score", "ROC-AUC", "PR-AUC", "FPR", "FNR", "TP", "FP", "TN", "FN"]
    ]
    df.to_csv(os.path.join(OUTPUT_DIR, "metrics_table.csv"), index=False)
    print("  Saved -> outputs/metrics_table.csv")

    sep = "=" * 62
    lines = [
        sep,
        "  ATAF -- Step 6: Model Evaluation Report",
        sep,
        "",
        f"  Evaluation threshold: {THRESHOLD}",
        f"  Primary metric:       PR-AUC (best for imbalanced fraud data)",
        "",
        "  METRICS TABLE",
        "-" * 62,
        df.to_string(index=False),
        "",
        "-" * 62,
        "  CLASSIFICATION REPORTS",
        "",
    ]

    # Add per-model classification report
    for r in results:
        lines.append(f"  >> {r['Model']}")
        lines.append(f"     TP={r['TP']}  FP={r['FP']}  TN={r['TN']}  FN={r['FN']}")
        lines.append(f"     FPR={r['FPR']}  FNR={r['FNR']}")
        lines.append("")

    lines += [
        sep,
        "  MODEL SELECTION",
        sep,
        "",
        f"  Selected Model : {best['Model']}",
        f"  PR-AUC         : {best['PR-AUC']}",
        f"  ROC-AUC        : {best['ROC-AUC']}",
        f"  F1-Score       : {best['F1-Score']}",
        f"  Precision      : {best['Precision']}",
        f"  Recall         : {best['Recall']}",
        f"  FPR            : {best['FPR']}",
        f"  FNR            : {best['FNR']}",
        "",
        "  Rationale: PR-AUC is the primary criterion for fraud",
        "  detection because the test set is heavily imbalanced",
        "  (~3.5% fraud). PR-AUC punishes false positives much",
        "  more directly than ROC-AUC in this regime.",
        "",
        f"  This model will be used as the AI Risk Engine in Step 7.",
        sep,
    ]

    report = "\n".join(lines)
    print("\n" + report)
    with open(os.path.join(OUTPUT_DIR, "evaluation_report.txt"), "w", encoding="utf-8") as f:
        f.write(report)
    print("  Saved -> outputs/evaluation_report.txt")

    with open(os.path.join(OUTPUT_DIR, "best_model.txt"), "w", encoding="utf-8") as f:
        f.write(best["Model"])
    print(f"  Saved -> outputs/best_model.txt  ({best['Model']})")

# ---- Main --------------------------------------------------------------------
def main():
    print("=" * 62)
    print("  ATAF -- Step 6: Evaluate and Select the AI Model")
    print("=" * 62)

    X_test, y_test = load_test_data()

    print("\nLoading trained models from Step 5...")
    models = load_models()

    print("\nEvaluating models on the held-out test set...")
    results = []
    for name, model in models.items():
        print(f"  Evaluating {name}...")
        r = evaluate_model(model, X_test, y_test, name)
        results.append(r)
        print(f"    Precision={r['Precision']}  Recall={r['Recall']}  "
              f"F1={r['F1-Score']}  ROC-AUC={r['ROC-AUC']}  PR-AUC={r['PR-AUC']}  "
              f"FPR={r['FPR']}  FNR={r['FNR']}")

    print("\nGenerating plots...")
    plot_roc_curves(models, results, X_test, y_test)
    plot_pr_curves(models, results, X_test, y_test)
    plot_confusion_matrices(results)
    plot_metrics_bar(results)

    best = select_best_model(results)
    best_model_obj = models[best["Model"]]
    plot_threshold_analysis(best_model_obj, best["Model"], X_test, y_test)

    save_report(results, best)

    print(f"\nStep 6 complete! Selected model: {best['Model']}")
    print("Proceed to Step 7 -- Design the Adaptive Security Policy.")

if __name__ == "__main__":
    main()
