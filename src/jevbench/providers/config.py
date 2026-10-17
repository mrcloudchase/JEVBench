"""Provider definitions and the registry that resolves them.

Credentials never live in framework files. Providers are declared in a separate providers
file (YAML or JSON) whose string values may reference environment variables with
``${env:NAME}``, or purely through environment variables for the built-in ``typesafe`` provider.

Lookup order for the providers file: an explicit path, ``$JEVBENCH_PROVIDERS``,
``./jevbench.providers.yaml``, then ``~/.config/jevbench/providers.yaml``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from jevbench.errors import ProviderError
from jevbench.loader import read_data_file

_ENV_RE = re.compile(r"\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}")

DEFAULT_PROVIDER_NAME = "typesafe"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"

ClientKind = Literal["sdk", "http", "mock"]


class ProviderConfig(BaseModel):
    """One JEV-wire-compatible endpoint."""

    model_config = ConfigDict(extra="forbid")

    name: str
    base_url: str = DEFAULT_BASE_URL
    api_key: str | None = None
    default_model: str = DEFAULT_MODEL
    client: ClientKind = "sdk"
    path: str = "/v1/systemone"
    headers: dict[str, str] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=lambda: ["images", "box", "long_context"])
    timeout: float = 30.0
    max_retries: int = 2
    mock_answers: dict[str, Any] = Field(default_factory=dict)

    def has(self, capability: str) -> bool:
        return capability in self.capabilities

    def redacted(self) -> dict[str, Any]:
        data = self.model_dump()
        if data.get("api_key"):
            data["api_key"] = "***"
        return data


class ProviderRegistry:
    """Resolves provider names to configurations and caches one client per provider."""

    def __init__(self, providers: dict[str, ProviderConfig] | None = None, default: str | None = None):
        self._providers: dict[str, ProviderConfig] = dict(providers or {})
        self._clients: dict[str, Any] = {}
        self.default_name = default or (next(iter(self._providers)) if self._providers else DEFAULT_PROVIDER_NAME)

    # -- construction -----------------------------------------------------------------

    @classmethod
    def from_env(cls) -> "ProviderRegistry":
        """A registry with just the built-in TypeSafe provider from the standard env vars."""
        registry = cls()
        registry.add(_builtin_typesafe())
        return registry

    @classmethod
    def load(cls, path: str | Path | None = None) -> "ProviderRegistry":
        """Load the providers file (see module docstring) on top of the built-in provider."""
        registry = cls.from_env()
        located = _locate(path)
        if located is None:
            return registry
        data = _substitute_env(read_data_file(located))
        if not isinstance(data, dict):
            raise ProviderError(f"{located}: providers file must be a mapping")
        entries = data.get("providers", data)
        if not isinstance(entries, dict):
            raise ProviderError(f"{located}: 'providers' must be a mapping of name -> config")
        for name, spec in entries.items():
            if not isinstance(spec, dict):
                raise ProviderError(f"{located}: provider {name!r} must be a mapping")
            try:
                registry.add(ProviderConfig(name=name, **spec))
            except Exception as exc:  # pydantic validation
                raise ProviderError(f"{located}: provider {name!r}: {exc}") from None
        if isinstance(data.get("default"), str):
            registry.default_name = data["default"]
        return registry

    def add(self, provider: ProviderConfig) -> None:
        self._providers[provider.name] = provider
        self._clients.pop(provider.name, None)

    # -- lookup -----------------------------------------------------------------------

    def names(self) -> list[str]:
        return list(self._providers)

    def get(self, name: str | None = None) -> ProviderConfig:
        key = name or self.default_name
        try:
            return self._providers[key]
        except KeyError:
            raise ProviderError(f"unknown provider {key!r}; configured: {sorted(self._providers)}") from None

    def client(self, name: str | None = None):
        from jevbench.providers.clients import build_client

        config = self.get(name)
        if config.name not in self._clients:
            self._clients[config.name] = build_client(config)
        return self._clients[config.name]


def _builtin_typesafe() -> ProviderConfig:
    return ProviderConfig(
        name=DEFAULT_PROVIDER_NAME,
        base_url=os.environ.get("TYPESAFE_BASE_URL", DEFAULT_BASE_URL),
        api_key=os.environ.get("TYPESAFE_API_KEY"),
        default_model=os.environ.get("TYPESAFE_DEFAULT_MODEL", DEFAULT_MODEL),
    )


def _locate(explicit: str | Path | None) -> Path | None:
    candidates = [explicit, os.environ.get("JEVBENCH_PROVIDERS"), "jevbench.providers.yaml", "jevbench.providers.json",
                  Path.home() / ".config" / "jevbench" / "providers.yaml"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    if explicit:
        raise ProviderError(f"providers file not found: {explicit}")
    return None


def _substitute_env(value: Any) -> Any:
    if isinstance(value, str):
        def repl(match: re.Match) -> str:
            name = match.group(1)
            if name not in os.environ:
                raise ProviderError(f"environment variable {name} is not set")
            return os.environ[name]
        return _ENV_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(v) for v in value]
    return value
