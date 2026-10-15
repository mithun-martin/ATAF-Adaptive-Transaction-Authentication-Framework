"""
Step 11: Integration & Verification Test Suite for Experimental Comparison
==========================================================================
Validates empirical metrics, comparative inequalities, benchmark outputs,
and generated figures.
"""

import os
import json
import pytest
from benchmark_runner import ExperimentalComparisonRunner, RESULTS_DIR


@pytest.fixture(scope="module")
def benchmark_data():
    runner = ExperimentalComparisonRunner()
    return runner.run_full_comparison()


def test_results_files_exist(benchmark_data):
    """Verifies all required experimental tables and plots were generated."""
    json_path = os.path.join(RESULTS_DIR, "comparative_metrics.json")
    csv_path = os.path.join(RESULTS_DIR, "comparative_metrics.csv")
    attack_csv = os.path.join(RESULTS_DIR, "attack_benchmark_results.csv")

    assert os.path.exists(json_path) and os.path.getsize(json_path) > 0
    assert os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
    assert os.path.exists(attack_csv) and os.path.getsize(attack_csv) > 0

    expected_plots = [
        "security_vs_burden.png",
        "metrics_comparison_barchart.png",
        "attack_defense_comparison.png",
        "friction_tradeoff_curve.png",
    ]
    for p in expected_plots:
        plot_file = os.path.join(RESULTS_DIR, p)
        assert os.path.exists(plot_file) and os.path.getsize(plot_file) > 1000, f"Missing or empty plot: {p}"


def test_security_inequalities(benchmark_data):
    """
    Validates empirical security relationships:
    - System 1 has 100% Attack Success Rate (Vulnerable)
    - System 2 and System 3 achieve 0% Attack Success Rate (Protected)
    - System 3 achieves high ROC-AUC (>0.90) and PR-AUC (>0.60)
    """
    soc = benchmark_data["social_engineering_metrics"]
    ds = benchmark_data["dataset_security_metrics"]

    # Attack Success Rates
    assert soc["system_1"]["attack_success_rate"] == 100.0
    assert soc["system_2"]["attack_success_rate"] == 0.0
    assert soc["system_3"]["attack_success_rate"] == 0.0

    # Fraud Detection Rates
    assert soc["system_1"]["fraud_detection_rate"] == 0.0
    assert soc["system_2"]["fraud_detection_rate"] == 100.0
    assert soc["system_3"]["fraud_detection_rate"] == 100.0

    # Large-Scale ML metrics for System 3
    assert ds["system_3"]["roc_auc"] >= 0.90
    assert ds["system_3"]["pr_auc"] >= 0.60
    assert ds["system_3"]["far"] <= 0.15


def test_usability_inequalities(benchmark_data):
    """
    Validates empirical usability relationships:
    - System 3 step count is significantly lower than System 2 (2.05 vs 3.0)
    - System 3 completion time is substantially lower than System 2 (18.1s vs 32.2s)
    - System 3 confines step-up 3FA to less than 10% of total transactions
    """
    ub = benchmark_data["usability_burden_metrics"]

    # Authentication Steps
    assert ub["system_1"]["mean_steps"] == 2.0
    assert ub["system_2"]["mean_steps"] == 3.0
    assert ub["system_3"]["mean_steps"] < 2.5
    assert ub["system_3"]["mean_steps"] < ub["system_2"]["mean_steps"]

    # Authentication Time
    assert ub["system_3"]["mean_auth_time_seconds"] < ub["system_2"]["mean_auth_time_seconds"]
    time_saved = ub["system_2"]["mean_auth_time_seconds"] - ub["system_3"]["mean_auth_time_seconds"]
    assert time_saved >= 10.0, f"Expected >10s time saved per tx, got {time_saved}s"

    # Step-Up Rate
    assert ub["system_1"]["step_up_rate_pct"] == 0.0
    assert ub["system_2"]["step_up_rate_pct"] == 100.0
    assert ub["system_3"]["step_up_rate_pct"] < 10.0, "Step 3 should confine step-up to <10% of traffic"
