import os
from pathlib import Path

import pytest

from jevbench.providers.config import ProviderConfig, ProviderRegistry

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def mock_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.add(ProviderConfig(name="typesafe", client="mock"))
    registry.add(ProviderConfig(name="mock", client="mock", mock_answers={"department": "billing"}))
    registry.default_name = "typesafe"
    return registry


@pytest.fixture
def examples() -> Path:
    return EXAMPLES


@pytest.fixture
def store_root(tmp_path, monkeypatch):
    root = tmp_path / "store"
    monkeypatch.setenv("JEVBENCH_STORE", str(root))
    return root
