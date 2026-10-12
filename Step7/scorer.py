"""
Step 7: AI Transaction Risk Scorer
===================================
Loads the trained XGBoost model from Step 5 / Step 6 to score incoming
transactions and outputs calibrated risk probabilities R in [0.0, 1.0]
along with human-readable risk indicators.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, Tuple, List, Optional

# Default path to serialized model from Step 5
DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "Step5", "models", "xgboost.pkl"
)


class RiskScorer:
    """
    AI Risk Inference Engine.
    Loads XGBoost classifier and evaluates transaction risk.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.model = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        """Attempts to load serialized XGBoost model."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_loaded = True
            except Exception as e:
                print(f"[Warning] Failed to load model from {self.model_path}: {e}")
                self.model = None
                self.is_loaded = False
        else:
            self.model = None
            self.is_loaded = False

    def score_transaction(self, tx: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Calculates transaction risk score in [0.0, 1.0] and extracts risk explanations.

        Supported transaction fields:
        - amount: float (transfer amount in currency units)
        - user_avg_amount: float (user's historical typical transaction amount)
        - is_new_beneficiary: bool (whether recipient was added recently)
        - hour_of_day: int (0 to 23)
        - velocity_last_hour: int (count of transfers in last 60 minutes)
        - raw_features: Optional array/dict of 359 IEEE-CIS features if available
        """
        risk_factors: List[str] = []
        base_score = 0.05  # baseline background risk

        amount = float(tx.get("amount", 0.0))
        user_avg = float(tx.get("user_avg_amount", 5000.0))
        is_new_ben = bool(tx.get("is_new_beneficiary", False))
        hour = int(tx.get("hour_of_day", 12))
        velocity = int(tx.get("velocity_last_hour", 0))

        # 1. Feature Analysis: Amount Deviation
        amount_ratio = amount / max(user_avg, 1.0)
        if amount_ratio >= 10.0 or amount >= 50000:
            base_score += 0.45
            risk_factors.append(f"Transfer amount (₹{amount:,.2f}) is {amount_ratio:.1f}x higher than typical historical volume")
        elif amount_ratio >= 3.0 or amount >= 25000:
            base_score += 0.25
            risk_factors.append(f"Transfer amount (₹{amount:,.2f}) moderately exceeds typical baseline")

        # 2. Feature Analysis: Recipient Trust
        if is_new_ben:
            base_score += 0.20
            risk_factors.append("Recipient is a new beneficiary added within the last 24 hours")

        # 3. Feature Analysis: High-Risk Time Window (Social engineering often occurs late night / early hours)
        if 1 <= hour <= 5:
            base_score += 0.15
            risk_factors.append(f"Transaction initiated during high-fraud night hours ({hour:02d}:00 hrs)")

        # 4. Feature Analysis: High Velocity
        if velocity >= 3:
            base_score += 0.30
            risk_factors.append(f"High transaction frequency detected ({velocity} transfers initiated in the past hour)")
        elif velocity == 2:
            base_score += 0.10
            risk_factors.append(f"Elevated frequency ({velocity} transfers in the past hour)")

        # 5. Direct ML Model Integration (if full feature vector provided and model loaded)
        if self.is_loaded and "raw_features" in tx:
            try:
                raw_feats = np.array(tx["raw_features"]).reshape(1, -1)
                ml_prob = float(self.model.predict_proba(raw_feats)[0, 1])
                # Blend ML probability with contextual indicators
                final_score = 0.60 * ml_prob + 0.40 * base_score
                if ml_prob > 0.6:
                    risk_factors.append(f"XGBoost AI model flagged tabular anomaly patterns (ML probability: {ml_prob:.4f})")
            except Exception as e:
                final_score = base_score
        else:
            final_score = base_score

        # Clamp between 0.01 and 0.99
        final_score = float(np.clip(final_score, 0.01, 0.99))
        return final_score, risk_factors
