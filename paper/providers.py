"""Providers: anything that turns state and questions into a belief over HTTP.

Provider is the generic HTTP client. It owns transport, configuration, retries and errors, and leaves
three things to subclasses: headers(), payload() and parse(). A provider with a different API is one
subclass that overrides what differs. parse() must return {"model", "answers", "usage"} with answers
in the typed-decision wire format, so nothing downstream changes when the provider does.

Configuration comes from the environment (usually .env):

    PROVIDER           registered name (typesafe) or "module:Class"; default typesafe
    PROVIDER_URL       endpoint; optional when the class has a default
    PROVIDER_API_KEY   required
    PROVIDER_MODEL     optional when the class has a default
"""

from __future__ import annotations

import importlib
import json
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

PROVIDERS: dict[str, type["Provider"]] = {}


def register(name: str):
    """Class decorator: make a provider selectable by name."""
    def add(cls):
        PROVIDERS[name] = cls
        return cls
    return add


class Provider(ABC):
    """Generic HTTP provider: state + questions -> {model, answers, usage}."""

    url: str | None = None                 # class defaults; the environment overrides them
    model: str | None = None
    retry_statuses = {408, 429, 500, 502, 503, 504, 529}

    def __init__(self, url=None, api_key=None, model=None, timeout=30.0, retries=3):
        self.url, self.api_key, self.model = url or self.url, api_key, model or self.model
        self.timeout, self.retries = timeout, retries
        for field in ("url", "api_key", "model"):
            if not getattr(self, field):
                raise RuntimeError(f"{type(self).__name__}: set PROVIDER_{field.upper()} in .env or the environment")

    @classmethod
    def from_env(cls, env=os.environ) -> "Provider":
        return cls(url=env.get("PROVIDER_URL"), api_key=env.get("PROVIDER_API_KEY"), model=env.get("PROVIDER_MODEL"))

    # ---- what a provider defines
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @abstractmethod
    def payload(self, state, questions: dict) -> dict:
        """The request body for one belief."""

    @abstractmethod
    def parse(self, body: dict) -> dict:
        """The response body -> {"model", "answers", "usage"}, answers in the wire format."""

    # ---- what every provider shares
    def __call__(self, state, questions: dict) -> dict:
        data = json.dumps(self.payload(state, questions)).encode("utf-8")
        for attempt in range(self.retries + 1):
            request = urllib.request.Request(self.url, data=data, headers=self.headers(), method="POST")
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return self.parse(json.loads(response.read()))
            except urllib.error.HTTPError as err:
                detail = err.read().decode("utf-8", "replace")[:300]
                if err.code not in self.retry_statuses or attempt == self.retries:
                    raise RuntimeError(f"HTTP {err.code} from {self.url}: {detail}") from None
                time.sleep(float(err.headers.get("Retry-After") or 2 ** attempt))
            except (urllib.error.URLError, TimeoutError) as err:
                if attempt == self.retries:
                    raise RuntimeError(f"{self.url}: {err}") from None
                time.sleep(2 ** attempt)


@register("typesafe")
class TypeSafe(Provider):
    """The TypeSafe wire format. Also any gateway that serves the same body at another URL."""

    url = "https://api.typesafe.ai/v1/systemone"
    model = "jev-latest"

    def payload(self, state, questions):
        return {"model": self.model, "state": state, "questions": questions}

    def parse(self, body):
        return {"model": body.get("model"), "answers": body["answers"], "usage": body.get("usage", {})}


def load_provider(env=os.environ) -> Provider:
    """The provider named by PROVIDER (a registered name or "module:Class"), configured from env."""
    name = env.get("PROVIDER", "typesafe")
    if name in PROVIDERS:
        cls = PROVIDERS[name]
    else:
        module, _, attr = name.partition(":")
        cls = getattr(importlib.import_module(module), attr)
    return cls.from_env(env)
