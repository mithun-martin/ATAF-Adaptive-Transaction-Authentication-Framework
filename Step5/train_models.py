"""
Step 5 -- Develop the AI Transaction Risk Model
================================================
Trains three models on the processed IEEE-CIS dataset:
  1. Logistic Regression  (baseline linear model)
  2. Random Forest        (ensemble tree model)
  3. XGBoost              (gradient-boosted trees -- primary candidate)

Each model outputs a probability risk score (0.0 -> 1.0).
Models and feature-importance plots are saved to the outputs/ folder.

Usage:
    python train_models.py

Output:
    outputs/logistic_regression.pkl
    outputs/random_forest.pkl
    outputs/xgboost.pkl
    outputs/feature_importance_rf.png
    outputs/feature_importance_xgb.png
    outputs/risk_score_distribution.png
    outputs/model_summary.txt
"""

import os
import sys
import time
import joblib

# Force UTF-8 output so special chars print safely on Windows terminals
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving plots
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

# ─── Config ───────────────────────────────────────────────────────────────────
PROCESSED_DIR = "../Step4/data/processed"
OUTPUT_DIR    = "outputs"
MODELS_DIR    = "models"
TARGET        = "isFraud"
RANDOM_STATE  = 42
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# ─── Load Data ────────────────────────────────────────────────────────────────
def load_data():
    print("Loading processed datasets from Step 4...")
    train = pd.read_parquet(os.path.join(PROCESSED_DIR, "train_processed.parquet"))
    val   = pd.read_parquet(os.path.join(PROCESSED_DIR, "val_processed.parquet"))

    X_train = train.drop(columns=[TARGET])
    y_train = train[TARGET]
    X_val   = val.drop(columns=[TARGET])
    y_val   = val[TARGET]

    print(f"  Train: {X_train.shape} | Fraud rate: {y_train.mean()*100:.2f}%")
    print(f"  Val:   {X_val.shape}   | Fraud rate: {y_val.mean()*100:.2f}%")
    return X_train, y_train, X_val, y_val


# ─── Feature names (needed after scaling) ────────────────────────────────────
def get_feature_names(X_train):
    return list(X_train.columns)


# ─── Model 1: Logistic Regression ────────────────────────────────────────────
def train_logistic_regression(X_train, y_train, X_val, y_val, feature_names):
    print("\n[1/3] Training Logistic Regression...")
    t0 = time.time()

    # LR needs scaled features
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(
            max_iter=1000,
            class_weight="balanced",   # handles remaining imbalance
            C=0.1,
            solver="lbfgs",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ])
    pipe.fit(X_train, y_train)
    elapsed = time.time() - t0

    val_probs = pipe.predict_proba(X_val)[:, 1]
    print(f"  Done in {elapsed:.1f}s | Val mean risk score: {val_probs.mean():.4f}")

    joblib.dump(pipe, os.path.join(MODELS_DIR, "logistic_regression.pkl"))
    print("  Saved -> models/logistic_regression.pkl")
    return pipe, val_probs


# ─── Model 2: Random Forest ──────────────────────────────────────────────────
def train_random_forest(X_train, y_train, X_val, y_val, feature_names):
    print("\n[2/3] Training Random Forest...")
    t0 = time.time()

    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=20,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=0,
    )
    rf.fit(X_train, y_train)
    elapsed = time.time() - t0

    val_probs = rf.predict_proba(X_val)[:, 1]
    print(f"  Done in {elapsed:.1f}s | Val mean risk score: {val_probs.mean():.4f}")

    joblib.dump(rf, os.path.join(MODELS_DIR, "random_forest.pkl"))
    print("  Saved -> models/random_forest.pkl")

    # Feature importance plot (top 20)
    importances = pd.Series(rf.feature_importances_, index=feature_names)
    top20 = importances.nlargest(20).sort_values()
    fig, ax = plt.subplots(figsize=(10, 7))
    top20.plot(kind="barh", ax=ax, color="steelblue")
    ax.set_title("Random Forest -- Top 20 Feature Importances")
    ax.set_xlabel("Mean Decrease in Impurity")
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "feature_importance_rf.png"), dpi=150)
    plt.close(fig)
    print("  Saved -> outputs/feature_importance_rf.png")

    return rf, val_probs


# ─── Model 3: XGBoost ────────────────────────────────────────────────────────
def train_xgboost(X_train, y_train, X_val, y_val, feature_names):
    print("\n[3/3] Training XGBoost...")
    t0 = time.time()

    # Compute scale_pos_weight to handle any residual imbalance
    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale_pos_weight = neg / pos
    print(f"  scale_pos_weight = {scale_pos_weight:.2f} (neg={neg}, pos={pos})")

    xgb = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        use_label_encoder=False,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=0,
        early_stopping_rounds=30,
    )
    xgb.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    elapsed = time.time() - t0

    val_probs = xgb.predict_proba(X_val)[:, 1]
    print(f"  Done in {elapsed:.1f}s | Best iteration: {xgb.best_iteration}")
    print(f"  Val mean risk score: {val_probs.mean():.4f}")

    joblib.dump(xgb, os.path.join(MODELS_DIR, "xgboost.pkl"))
    print("  Saved -> models/xgboost.pkl")

    # Feature importance plot (top 20 by gain)
    importances = pd.Series(
        xgb.get_booster().get_score(importance_type="gain")
    ).nlargest(20).sort_values()
    fig, ax = plt.subplots(figsize=(10, 7))
    importances.plot(kind="barh", ax=ax, color="darkorange")
    ax.set_title("XGBoost -- Top 20 Feature Importances (Gain)")
    ax.set_xlabel("Gain")
    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "feature_importance_xgb.png"), dpi=150)
    plt.close(fig)
    print("  Saved -> outputs/feature_importance_xgb.png")

    return xgb, val_probs


# ─── Risk Score Distribution Plot ────────────────────────────────────────────
def plot_risk_distributions(y_val, probs_dict):
    """Overlay risk score distributions for fraud vs non-fraud per model."""
    fig, axes = plt.subplots(1, len(probs_dict), figsize=(6 * len(probs_dict), 5))
    if len(probs_dict) == 1:
        axes = [axes]

    for ax, (name, probs) in zip(axes, probs_dict.items()):
        df_plot = pd.DataFrame({"risk_score": probs, "isFraud": y_val.values})
        for label, color, lbl in [(0, "steelblue", "Legitimate"), (1, "crimson", "Fraud")]:
            subset = df_plot[df_plot["isFraud"] == label]["risk_score"]
            ax.hist(subset, bins=50, alpha=0.6, color=color, label=lbl, density=True)
        ax.set_title(f"{name}\nRisk Score Distribution")
        ax.set_xlabel("Risk Score (probability)")
        ax.set_ylabel("Density")
        ax.legend()

    plt.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "risk_score_distribution.png"), dpi=150)
    plt.close(fig)
    print("\n  Saved -> outputs/risk_score_distribution.png")


# ─── Summary ─────────────────────────────────────────────────────────────────
def save_summary(results: dict):
    lines = [
        "=" * 60,
        "  ATAF -- Step 5 Model Training Summary",
        "=" * 60,
        "",
        "Models trained on balanced IEEE-CIS Fraud Detection dataset.",
        "Risk score = P(isFraud=1) output from predict_proba().",
        "",
    ]
    for name, info in results.items():
        lines.append(f"  {name}")
        for k, v in info.items():
            lines.append(f"    {k}: {v}")
        lines.append("")

    lines += [
        "Next -> Step 6: Evaluate and select the best model",
        "  Run: python ../Step6/evaluate_models.py",
        "=" * 60,
    ]
    summary = "\n".join(lines)
    print("\n" + summary)
    with open(os.path.join(OUTPUT_DIR, "model_summary.txt"), "w") as f:
        f.write(summary)
    print("  Saved -> outputs/model_summary.txt")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  ATAF -- Step 5: AI Transaction Risk Model Training")
    print("=" * 60)

    X_train, y_train, X_val, y_val = load_data()
    feature_names = get_feature_names(X_train)

    # Convert to float32 once to keep memory low for all models
    X_train = X_train.astype(np.float32)
    X_val   = X_val.astype(np.float32)

    probs_dict = {}
    results    = {}

    # 1. Logistic Regression
    lr_model, lr_probs = train_logistic_regression(X_train, y_train, X_val, y_val, feature_names)
    probs_dict["Logistic Regression"] = lr_probs
    results["Logistic Regression"] = {
        "saved_to": "models/logistic_regression.pkl",
        "val_mean_risk_score": f"{lr_probs.mean():.4f}",
    }

    # 2. Random Forest
    rf_model, rf_probs = train_random_forest(X_train, y_train, X_val, y_val, feature_names)
    probs_dict["Random Forest"] = rf_probs
    results["Random Forest"] = {
        "saved_to": "models/random_forest.pkl",
        "val_mean_risk_score": f"{rf_probs.mean():.4f}",
        "feature_importance_plot": "outputs/feature_importance_rf.png",
    }

    # 3. XGBoost
    xgb_model, xgb_probs = train_xgboost(X_train, y_train, X_val, y_val, feature_names)
    probs_dict["XGBoost"] = xgb_probs
    results["XGBoost"] = {
        "saved_to": "models/xgboost.pkl",
        "val_mean_risk_score": f"{xgb_probs.mean():.4f}",
        "feature_importance_plot": "outputs/feature_importance_xgb.png",
    }

    # Risk score distribution overlay
    plot_risk_distributions(y_val, probs_dict)

    # Summary
    save_summary(results)

    print("\n✅ Step 5 complete! All models saved to models/")
    print("   Run Step 6 (evaluate_models.py) to compare and select the best model.")


if __name__ == "__main__":
    main()
