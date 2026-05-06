"""ObjectNode — 所有节点的抽象基类."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PortDef:
    """端口定义 — 描述一个输入或输出端口的元数据."""
    id: str
    label: str
    dtype: str = "tensor"
    required: bool = True


@dataclass
class ObjectNodeMeta:
    """节点元数据 — 前端据此动态渲染节点面板和参数表单."""
    display_name: str
    category: str
    description: str = ""
    params_schema: dict[str, Any] = field(default_factory=dict)
    ports: dict[str, list[PortDef]] = field(default_factory=dict)


class ObjectNode(ABC):
    """所有节点的抽象基类.

    每个子类通过 meta 属性声明自己的元数据，并由 @register_node
    装饰器注册到全局注册表。前端通过 GET /api/nodes 自动发现。
    """

    meta: ObjectNodeMeta

    @abstractmethod
    def infer_output_shape(
        self, input_shapes: list[tuple[int, ...]], params: dict
    ) -> list[tuple[int, ...]]:
        """根据输入 shape 和参数推断输出 shape（构建期使用）."""

    @abstractmethod
    def to_pytorch_init(self, layer_name: str, params: dict) -> str:
        """返回 __init__ 中的层实例化语句."""

    @abstractmethod
    def to_pytorch_forward(
        self, layer_name: str, input_vars: list[str], output_vars: list[str], params: dict
    ) -> str:
        """返回 forward 中的调用语句."""
