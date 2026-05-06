"""全局节点注册表 — 所有 ObjectNode 子类通过装饰器注册到这里."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .object_node import ObjectNode

_NODE_REGISTRY: dict[str, type["ObjectNode"]] = {}


def register_node(node_type: str):
    """装饰器：将 ObjectNode 子类注册到全局注册表."""

    def decorator(cls: type["ObjectNode"]) -> type["ObjectNode"]:
        _NODE_REGISTRY[node_type] = cls
        return cls

    return decorator


def get_all_meta() -> dict[str, dict]:
    """返回所有已注册节点的元数据，供 GET /api/nodes 使用."""
    return {
        node_type: {
            "display_name": cls.meta.display_name,
            "category": cls.meta.category,
            "description": cls.meta.description,
            "params_schema": cls.meta.params_schema,
            "ports": {
                "inputs": [
                    {"id": p.id, "label": p.label, "dtype": p.dtype, "required": p.required}
                    for p in cls.meta.ports.get("inputs", [])
                ],
                "outputs": [
                    {"id": p.id, "label": p.label, "dtype": p.dtype, "required": p.required}
                    for p in cls.meta.ports.get("outputs", [])
                ],
            },
        }
        for node_type, cls in _NODE_REGISTRY.items()
    }


def get_node_class(node_type: str) -> type["ObjectNode"] | None:
    """根据类型名查找已注册的节点类."""
    return _NODE_REGISTRY.get(node_type)
