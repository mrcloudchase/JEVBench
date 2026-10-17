"""Saving, loading and versioning frameworks on disk.

Layout: ``<root>/<name>/<version>.yaml`` plus ``<root>/<name>/latest`` holding the newest
version string. References of the form ``name@version`` (or ``name`` for latest) resolve here;
anything else is treated as a file path.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from jevbench.errors import SchemaError, StoreError
from jevbench.loader import dump_yaml, read_data_file
from jevbench.schema.models import Framework

_REF_RE = re.compile(r"^([A-Za-z0-9_.-]+)(?:@([A-Za-z0-9_.+-]+))?$")


def framework_from_data(data: Any, label: str = "<framework>") -> Framework:
    if not isinstance(data, dict):
        raise SchemaError(f"{label}: framework must be a mapping")
    try:
        return Framework(**data)
    except ValidationError as exc:
        problems = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "-"
            problems.append(f"{label}: {loc}: {err['msg']}")
        raise SchemaError(problems) from None


def load_framework_file(path: str | Path) -> tuple[Framework, Path]:
    path = Path(path)
    framework = framework_from_data(read_data_file(path), str(path))
    return framework, path.resolve().parent


class FrameworkStore:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or os.environ.get("JEVBENCH_STORE") or Path.home() / ".jevbench" / "frameworks")

    def save(self, framework: Framework, *, overwrite: bool = False) -> Path:
        folder = self.root / framework.name
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{framework.version}.yaml"
        if target.exists() and not overwrite:
            raise StoreError(f"{framework.name}@{framework.version} already exists at {target}; bump 'version' or pass overwrite")
        target.write_text(dump_yaml(framework.to_dict()), encoding="utf-8")
        (folder / "latest").write_text(framework.version, encoding="utf-8")
        return target

    def path_for(self, name: str, version: str | None = None) -> Path:
        folder = self.root / name
        if not folder.is_dir():
            raise StoreError(f"no framework named {name!r} in store {self.root}")
        if version is None:
            try:
                version = (folder / "latest").read_text(encoding="utf-8").strip()
            except OSError:
                raise StoreError(f"framework {name!r} has no 'latest' pointer") from None
        target = folder / f"{version}.yaml"
        if not target.is_file():
            raise StoreError(f"no version {version!r} of {name!r} (have: {', '.join(self.versions(name))})")
        return target

    def load(self, name: str, version: str | None = None) -> tuple[Framework, Path]:
        return load_framework_file(self.path_for(name, version))

    def versions(self, name: str) -> list[str]:
        folder = self.root / name
        return sorted(p.stem for p in folder.glob("*.yaml")) if folder.is_dir() else []

    def list(self) -> list[dict[str, Any]]:
        if not self.root.is_dir():
            return []
        entries = []
        for folder in sorted(p for p in self.root.iterdir() if p.is_dir()):
            latest = (folder / "latest").read_text(encoding="utf-8").strip() if (folder / "latest").is_file() else None
            entries.append({"name": folder.name, "latest": latest, "versions": self.versions(folder.name)})
        return entries


def resolve_reference(ref: str, base_dir: Path, store: FrameworkStore | None = None) -> tuple[Framework, Path]:
    """Resolve a ``framework:`` reference to a loaded framework and its base directory."""
    candidate = Path(ref)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    if candidate.is_file():
        return load_framework_file(candidate)
    match = _REF_RE.match(ref)
    if match and "/" not in ref and not ref.endswith((".yaml", ".yml", ".json")):
        return (store or FrameworkStore()).load(match.group(1), match.group(2))
    raise StoreError(f"framework reference {ref!r} is neither a file (relative to {base_dir}) nor a store entry")
