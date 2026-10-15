"""
Step 10: Attack Scenario Catalog Loader & Management
=====================================================
Loads, filters, and manages standardized social-engineering attack scenarios.
"""

import json
import os
from typing import List, Optional
from scenarios.models import AttackScenario, AttackCategory, SeverityLevel

DEFAULT_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "scenarios.json")


class ScenarioCatalog:
    """Provides structured programmatic access to all attack and control scenarios."""

    def __init__(self, catalog_path: Optional[str] = None):
        self.catalog_path = catalog_path or DEFAULT_CATALOG_PATH
        self._scenarios: List[AttackScenario] = []
        self._load()

    def _load(self):
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._scenarios = [AttackScenario(**item) for item in data]

    def all(self) -> List[AttackScenario]:
        """Returns all registered scenarios."""
        return list(self._scenarios)

    def get(self, scenario_id: str) -> Optional[AttackScenario]:
        """Look up scenario by unique ID."""
        for s in self._scenarios:
            if s.id.lower() == scenario_id.lower():
                return s
        return None

    def filter_by_category(self, category: AttackCategory) -> List[AttackScenario]:
        """Filter scenarios by attack category."""
        return [s for s in self._scenarios if s.category == category]

    def get_fraud_scenarios(self) -> List[AttackScenario]:
        """Returns all simulated social-engineering attacks."""
        return [s for s in self._scenarios if s.is_fraud]

    def get_control_scenarios(self) -> List[AttackScenario]:
        """Returns legitimate benign baseline control scenarios."""
        return [s for s in self._scenarios if not s.is_fraud]

    def count(self) -> int:
        return len(self._scenarios)


default_catalog = ScenarioCatalog()
