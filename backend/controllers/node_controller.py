"""节点管理控制器 — 编排节点查询与自定义节点注册."""

import ast
import importlib.util
import sys
from pathlib import Path

from api.response import (
    CODE_CUSTOM_CANNOT_REMOVE_BUILTIN,
    CODE_CUSTOM_NOT_FOUND,
    CODE_CUSTOM_NOT_OBJECTNODE,
    CODE_CUSTOM_SAFETY_BANNED,
)
from nodes.object_node import ObjectNode
from nodes.registry import _NODE_REGISTRY, get_all_meta, get_node_class

CUSTOM_NODES_DIR = Path(__file__).resolve().parent.parent / "custom_nodes"
CUSTOM_NODES_DIR.mkdir(exist_ok=True)

BANNED_BUILTINS = {"exec", "eval", "compile", "__import__", "open", "globals", "locals"}
BANNED_MODULES = {"os", "sys", "subprocess", "shutil", "socket", "pickle", "ctypes", "signal", "atexit"}
BUILTIN_NODES = {"Input", "Output", "Linear", "ReLU", "Sigmoid", "GELU", "SiLU", "Tanh", "Softmax", "Add", "Concat", "Split", "Reshape", "Permute", "Squeeze", "Unsqueeze", "BatchNorm1d", "BatchNorm2d", "LayerNorm", "GroupNorm", "RMSNorm", "Dropout", "AlphaDropout", "Conv1d", "Conv2d", "Conv3d", "MaxPool2d", "AvgPool2d", "AdaptiveAvgPool2d", "Embedding"}


class ControllerError(Exception):
    """控制器层业务异常，携带业务状态码."""
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg


def list_all_nodes() -> dict:
    metas = get_all_meta()
    for nt in metas:
        metas[nt]["is_custom"] = nt not in BUILTIN_NODES
    return {"nodes": metas}


def register_custom(code: str) -> dict:
    # AST 安全检查
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_BUILTINS:
                raise ControllerError(CODE_CUSTOM_SAFETY_BANNED,
                    f"Banned function in custom node code: {node.func.id}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in BANNED_MODULES:
                    raise ControllerError(CODE_CUSTOM_SAFETY_BANNED,
                        f"Banned import in custom node code: {alias.name}")
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in BANNED_MODULES:
                raise ControllerError(CODE_CUSTOM_SAFETY_BANNED,
                    f"Banned import in custom node code: {node.module}")

    # 写入并动态加载
    filename = f"_custom_{abs(hash(code))}.py"
    filepath = CUSTOM_NODES_DIR / filename
    filepath.write_text(code, encoding="utf-8")

    spec = importlib.util.spec_from_file_location(filename.rstrip(".py"), str(filepath))
    if spec is None or spec.loader is None:
        raise ControllerError(CODE_CUSTOM_NOT_OBJECTNODE, "Failed to load module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # 找出新注册的节点
    known_before = set(BUILTIN_NODES)
    new_keys = [k for k in _NODE_REGISTRY if k not in known_before]

    registered = []
    for key in new_keys:
        cls = get_node_class(key)
        if cls is None or not issubclass(cls, ObjectNode):
            continue
        registered.append({
            "node_type": key,
            "display_name": cls.meta.display_name,
            "category": cls.meta.category,
        })

    if not registered:
        for key in new_keys:
            _NODE_REGISTRY.pop(key, None)
        filepath.unlink()
        raise ControllerError(CODE_CUSTOM_NOT_OBJECTNODE,
            "No valid ObjectNode subclass found. "
            "Use @register_node decorator and inherit from ObjectNode.")

    return {"nodes": registered}


def unregister_custom(node_type: str) -> dict:
    if node_type in BUILTIN_NODES:
        raise ControllerError(CODE_CUSTOM_CANNOT_REMOVE_BUILTIN,
            "Cannot remove built-in node type")
    if node_type not in _NODE_REGISTRY:
        raise ControllerError(CODE_CUSTOM_NOT_FOUND,
            f"Node type '{node_type}' not found")
    del _NODE_REGISTRY[node_type]
    return {}
