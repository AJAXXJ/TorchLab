"""Pydantic 请求/响应数据模型 (Model 层)."""

from typing import Any

from pydantic import BaseModel, Field


# ── 请求体 ──────────────────────────────────────────────────────


class GenerateRequest(BaseModel):
    nodes: list[dict[str, Any]]
    links: list[list[Any]]


class CustomNodeRegisterRequest(BaseModel):
    code: str = Field(..., description="Python source code of the custom node class")


# ── 响应 data 字段子模型 ─────────────────────────────────────────


class NodePortSchema(BaseModel):
    id: str
    label: str
    dtype: str = "tensor"
    required: bool = True


class ParamDefSchema(BaseModel):
    type: str
    default: Any = None
    required: bool = False
    min: int | float | None = None
    max: int | float | None = None
    options: list[str] | None = None
    description: str | None = None


class NodeMetaSchema(BaseModel):
    display_name: str
    category: str
    description: str = ""
    is_custom: bool = False
    params_schema: dict[str, ParamDefSchema] = Field(default_factory=dict)
    ports: dict[str, list[NodePortSchema]] = Field(default_factory=dict)


class GenerateData(BaseModel):
    code: str
    shapes: dict[str, list[int]] = Field(default_factory=dict)


class CustomNodeInfo(BaseModel):
    node_type: str
    display_name: str
    category: str


class CustomNodeRegisterData(BaseModel):
    nodes: list[CustomNodeInfo]


class CompositeExternalPort(BaseModel):
    node_id: int
    port_idx: int = 0
    label: str = ""


class CompositeCreateRequest(BaseModel):
    name: str = Field(..., description="组合节点名称")
    subgraph_nodes: list[dict[str, Any]]
    subgraph_links: list[list[Any]]
    external_inputs: list[CompositeExternalPort] = Field(default_factory=list)
    external_outputs: list[CompositeExternalPort] = Field(default_factory=list)
