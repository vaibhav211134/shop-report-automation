"""Shared pytest fixtures for report modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import yaml


@pytest.fixture()
def fixture_config() -> dict[str, Any]:
    """Load test configuration and sample rows."""
    fixture_path = Path(__file__).parent / "fixtures" / "test_config.yaml"
    with fixture_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture()
def sample_dataframe(fixture_config: dict[str, Any]) -> pd.DataFrame:
    """Return DataFrame built from fixture rows."""
    return pd.DataFrame(fixture_config["rows"])
