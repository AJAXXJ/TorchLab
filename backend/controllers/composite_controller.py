"""Composite node controller — port derivation, registration, and persistence."""
import json
from pathlib import Path

from nodes.registry import _NODE_REGISTRY, get_all_meta
from nodes.composite_node import CompositeNode
from nodes.object_node import ObjectNodeMeta, PortDef
from controllers.node_controller import ControllerError
from api.response import (
    CODE_OK, CODE_CUSTOM_SAFETY_BANNED, CODE_CUSTOM_NOT_OBJECTNODE,
)

COMPOSITE_DIR = Path(__file__).resolve().parent.parent / "custom_nodes"
COMPOSITE_DIR.mkdir(exist_ok=True)


def create_composite(
    name: str,
    subgraph: dict,
    external_inputs: list[dict],
    external_outputs: list[dict],
) -> dict:
    """从子图创建组合节点类型.

    Args:
        name: 组合节点名称 (也将作为注册类型名).
        subgraph: {"nodes": [...], "links": [...]} 格式的子图.
        external_inputs: [{"node_id": int, "port_idx": int, "label": str}, ...]
        external_outputs: [{"node_id": int, "port_idx": int, "label": str}, ...]

    Returns:
        {"node_type": str, "display_name": str, "category": str}
    """
    if name in _NODE_REGISTRY:
        raise ControllerError(CODE_CUSTOM_SAFETY_BANNED,
                              f"Node type '{name}' already exists")

    # Build port definitions (as PortDef objects)
    input_portdefs = [
        PortDef(id=f"in_{i}", label=ex.get("label", f"input_{i}"))
        for i, ex in enumerate(external_inputs)
    ]
    output_portdefs = [
        PortDef(id=f"out_{i}", label=ex.get("label", f"output_{i}"))
        for i, ex in enumerate(external_outputs)
    ]

    meta = ObjectNodeMeta(
        display_name=name,
        category="custom",
        description=f"Composite node: {name}",
        ports={"inputs": input_portdefs, "outputs": output_portdefs},
    )

    # Dynamically create a CompositeNode subclass
    cls = type(f"{name}Node", (CompositeNode,), {
        "meta": meta,
        "_subgraph_json": json.dumps(subgraph),
    })

    # Register in global registry
    _NODE_REGISTRY[name] = cls

    # Persist to JSON
    _persist_composite(name, subgraph, external_inputs, external_outputs)

    return {
        "node_type": name,
        "display_name": name,
        "category": "custom",
    }


def _persist_composite(name: str, subgraph: dict,
                       external_inputs: list[dict],
                       external_outputs: list[dict]) -> None:
    """持久化组合节点到磁盘."""
    filepath = COMPOSITE_DIR / f"composite_{name}.json"
    data = {
        "node_type": name,
        "display_name": name,
        "subgraph": subgraph,
        "external_inputs": external_inputs,
        "external_outputs": external_outputs,
    }
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_persisted_composites() -> int:
    """启动时扫描并加载持久化的组合节点. 返回加载数量."""
    count = 0
    for fpath in COMPOSITE_DIR.glob("composite_*.json"):
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            name = data["node_type"]
            if name in _NODE_REGISTRY:
                continue  # already registered (e.g., built-in with same name)

            input_portdefs = [
                PortDef(id=f"in_{i}", label=ex.get("label", f"input_{i}"))
                for i, ex in enumerate(data.get("external_inputs", []))
            ]
            output_portdefs = [
                PortDef(id=f"out_{i}", label=ex.get("label", f"output_{i}"))
                for i, ex in enumerate(data.get("external_outputs", []))
            ]
            meta = ObjectNodeMeta(
                display_name=name,
                category="custom",
                description=f"Composite node: {name}",
                ports={"inputs": input_portdefs, "outputs": output_portdefs},
            )

            cls = type(f"{name}Node", (CompositeNode,), {
                "meta": meta,
                "_subgraph_json": json.dumps(data["subgraph"]),
            })
            _NODE_REGISTRY[name] = cls
            count += 1
        except Exception:
            pass  # skip corrupted files
    return count


def remove_composite(name: str) -> None:
    """删除组合节点 (从注册表 + 磁盘)."""
    if name not in _NODE_REGISTRY:
        raise ControllerError(CODE_CUSTOM_NOT_OBJECTNODE,
                              f"Composite node '{name}' not found")

    del _NODE_REGISTRY[name]
    fpath = COMPOSITE_DIR / f"composite_{name}.json"
    if fpath.exists():
        fpath.unlink()
