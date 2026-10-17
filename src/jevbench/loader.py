"""Reading framework, input and provider files (YAML or JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from jevbench.errors import JevBenchError


def read_data_file(path: str | Path) -> Any:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise JevBenchError(f"cannot read {path}: {exc}") from None
    return parse_data(text, path.suffix, str(path))


def parse_data(text: str, suffix: str = ".yaml", label: str = "<string>") -> Any:
    try:
        if suffix.lower() == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise JevBenchError(f"{label}: cannot parse: {exc}") from None


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
