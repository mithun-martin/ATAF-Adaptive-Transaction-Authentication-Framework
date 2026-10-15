"""
Unit & Integration Tests for Step 12: Usability Evaluation
Responsible: Mithun + Aditya
"""

import json
from pathlib import Path
import pytest
import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent / "results"


@pytest.fixture(scope="module")
def usability_data():
    summary_path = RESULTS_DIR / "usability_summary.json"
    if not summary_path.exists():
        from usability_evaluator import run_full_evaluation
        run_full_evaluation()

    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_evaluation_artifacts_exist():
    required_files = [
        "usability_summary.json",
        "statistical_significance.json",
        "participant_trials.csv",
        "sus_scores.csv",
        "nasa_tlx_scores.csv",
        "user_burden_scores.csv",
        "sus_and_workload_comparison.png",
        "task_completion_time_by_scenario.png",
        "warning_comprehension_and_accuracy.png",
        "user_burden_radar_chart.png",
    ]
    for fname in required_files:
        fpath = RESULTS_DIR / fname
        assert fpath.exists(), f"Missing required artifact: {fname}"
        assert fpath.stat().st_size > 0, f"Artifact is empty: {fname}"


def test_sus_superiority(usability_data):
    metrics = usability_data["metrics"]
    stats_tests = usability_data["statistical_tests"]["sus"]

    s3_sus = metrics["System 3 (Proposed Adaptive)"]["sus_score"]
    s2_sus = metrics["System 2 (Static 3FA)"]["sus_score"]

    # System 3 SUS must be in Grade A range (> 80) and significantly higher than S2
    assert s3_sus > 80.0, f"System 3 SUS score should be Grade A, got {s3_sus}"
    assert s3_sus > s2_sus + 20.0, f"System 3 must outperform System 2 by at least 20 SUS points"
    assert stats_tests["p_val_s3_vs_s2"] < 0.001, "SUS difference must be statistically significant"
    assert stats_tests["cohens_d_s3_vs_s2"] > 2.0, "Effect size should be large (d > 2.0)"


def test_cognitive_workload_reduction(usability_data):
    metrics = usability_data["metrics"]
    stats_tests = usability_data["statistical_tests"]["nasa_tlx"]

    s3_tlx = metrics["System 3 (Proposed Adaptive)"]["nasa_tlx_workload"]
    s2_tlx = metrics["System 2 (Static 3FA)"]["nasa_tlx_workload"]

    assert s3_tlx < 35.0, f"Adaptive cognitive workload should be low, got {s3_tlx}"
    assert s2_tlx > 50.0, f"Static 3FA workload should reflect significant user burden, got {s2_tlx}"
    assert stats_tests["p_val_s3_vs_s2"] < 0.001, "TLX reduction must be statistically significant"


def test_routine_completion_time_savings(usability_data):
    routine_stats = usability_data["statistical_tests"]["routine_tct"]

    time_saved = routine_stats["time_saved_sec"]
    assert time_saved > 10.0, f"Adaptive system should save at least 10s on routine transfers, got {time_saved:.2f}s"
    assert routine_stats["p_val"] < 0.001, "Time savings must be statistically significant (p < 0.001)"


def test_habituation_and_warning_comprehension(usability_data):
    hci_stats = usability_data["statistical_tests"]["attack_security_hci"]

    # Static 3FA suffers from severe habituation blind clickthrough
    assert hci_stats["s2_habituation_blind_confirm_pct"] > 60.0, "Static 3FA should show high habituation clickthrough"
    assert hci_stats["s2_warning_comprehension_pct"] < 30.0, "Static 3FA warning comprehension should be degraded by habituation"

    # Adaptive breaks habituation with salient contextual cues
    assert hci_stats["s3_warning_comprehension_pct"] > 85.0, "Adaptive system must have high warning comprehension (>85%)"
    assert hci_stats["s3_detection_rate_pct"] > 85.0, "Adaptive system must enable high fraud detection/abort accuracy"
