"""Pydantic models for the universal framework schema (version 1).

A framework is a graph of typed nodes. The graph structure alone decides the architecture:
a single ``judge`` node is the smallest valid framework; councils, cascades, loops and
subgraphs are just more nodes and references. Node-type-specific fields are validated by the
node classes in the registry, so new node types extend the schema without touching this file.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = 1
NODE_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

Content = Any  # string | object | array, exactly as the JEV wire accepts


class Question(BaseModel):
    """One JEV question in wire form. Templates (``${...}``) are allowed in any content field."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["noul", "choice", "score", "box"]
    instructions: Content | None = None
    criteria: Content | None = None

    @model_validator(mode="after")
    def _check_shape(self) -> "Question":
        from jevbench.engine.expressions import is_template

        if is_template(self.criteria):
            return self  # resolved and re-validated at run time
        if self.type == "noul":
            if self.criteria is not None and not isinstance(self.criteria, dict):
                raise ValueError("noul criteria must be a mapping with 'true' and/or 'false'")
            if self.criteria is not None and not set(self.criteria) <= {"true", "false"}:
                raise ValueError("noul criteria keys must be 'true' and/or 'false'")
            if self.instructions is None and not self.criteria:
                raise ValueError("noul needs instructions or criteria")
        elif self.type == "choice":
            if not isinstance(self.criteria, dict) or not self.criteria:
                raise ValueError("choice criteria must be a non-empty mapping of option -> description")
            if len(self.criteria) > 255:
                raise ValueError("choice supports at most 255 options")
        elif self.type == "score":
            if not isinstance(self.criteria, list) or not 2 <= len(self.criteria) <= 10:
                raise ValueError("score criteria must be an ordered list of 2 to 10 levels")
        elif self.type == "box":
            if self.criteria is not None:
                raise ValueError("box questions take no criteria")
        return self

    def to_wire(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class NodeSpec(BaseModel):
    """Fields common to every node. Type-specific fields are kept in ``extra``."""

    model_config = ConfigDict(extra="allow")

    type: str
    description: str | None = None
    when: str | None = Field(default=None, description="Expression; the node is skipped when false.")
    depends_on: list[str] = Field(default_factory=list)

    @property
    def extra(self) -> dict[str, Any]:
        return dict(self.model_extra or {})


class InputSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    required: bool = True
    default: Any = None


class TestCase(BaseModel):
    """A declarative test: input, optional mocked rulings keyed by node path, expectations."""

    model_config = ConfigDict(extra="forbid")

    name: str
    input: dict[str, Any] = Field(default_factory=dict)
    mock: dict[str, Any] = Field(default_factory=dict, description="node path -> answers (or a list per loop iteration)")
    expect: list[str] = Field(default_factory=list, description="Expressions that must all be true.")
    expect_judgment: Any = None


class Defaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str | None = None
    model: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)


class Framework(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jevbench: int = Field(description="Schema version.")
    name: str = "framework"
    version: str = "0.1.0"
    description: str | None = None
    inputs: dict[str, InputSpec] = Field(default_factory=dict)
    defaults: Defaults = Field(default_factory=Defaults)
    nodes: dict[str, NodeSpec]
    output: Any = None
    tests: list[TestCase] = Field(default_factory=list)

    @field_validator("jevbench")
    @classmethod
    def _version(cls, value: int) -> int:
        if value != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema version {value}; this engine supports {SCHEMA_VERSION}")
        return value

    @field_validator("nodes")
    @classmethod
    def _node_ids(cls, nodes: dict[str, NodeSpec]) -> dict[str, NodeSpec]:
        if not nodes:
            raise ValueError("a framework needs at least one node")
        for node_id in nodes:
            if not NODE_ID_RE.match(node_id):
                raise ValueError(f"node id {node_id!r} must be an identifier (letters, digits, underscores)")
        return nodes

    @field_validator("inputs", mode="before")
    @classmethod
    def _inputs(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: ({} if v is None else v) for k, v in value.items()}
        return value

    @model_validator(mode="after")
    def _default_output(self) -> "Framework":
        if self.output is None:
            if len(self.nodes) == 1:
                self.output = f"nodes.{next(iter(self.nodes))}"
            else:
                raise ValueError("'output' is required when a framework has more than one node")
        return self

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class SubFramework(BaseModel):
    """An inline framework used as a loop body or an inline subgraph."""

    model_config = ConfigDict(extra="forbid")

    nodes: dict[str, NodeSpec]
    output: Any = None
    defaults: Defaults | None = None

    def as_framework(self, parent: Framework, name: str) -> Framework:
        return Framework(
            jevbench=SCHEMA_VERSION,
            name=name,
            version=parent.version,
            defaults=self.defaults or parent.defaults,
            nodes=self.nodes,
            output=self.output,
        )
