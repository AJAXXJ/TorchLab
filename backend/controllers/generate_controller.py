"""代码生成控制器 — 编排图构建 → shape推断 → 代码生成全流程."""

from api.response import (
    CODE_CODEGEN_FAILED,
    CODE_GRAPH_CYCLE,
    CODE_SHAPE_INFER_FAILED,
    CODE_UNKNOWN_NODE_TYPE,
)
from core.code_generator import generate_code
from core.graph_builder import GraphBuildError, build_graph
from core.shape_inferrer import ShapeInferError, infer_shapes


class ControllerError(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg


def _flatten_shapes(s: tuple) -> list | list[list]:
    """Flatten single-output shape tuple to list, keep multi-output as list of lists."""
    if len(s) == 1:
        return list(s[0])
    return [list(x) for x in s]


def execute_generate(nodes: list[dict], links: list[list]) -> dict:
    # 1. 图构建
    try:
        graph = build_graph(nodes, links)
    except GraphBuildError as e:
        if "cycle" in str(e).lower():
            raise ControllerError(CODE_GRAPH_CYCLE, str(e))
        raise ControllerError(CODE_UNKNOWN_NODE_TYPE, str(e))

    # 2. Shape 推断
    try:
        shapes = infer_shapes(graph)
    except ShapeInferError as e:
        raise ControllerError(CODE_SHAPE_INFER_FAILED, str(e))

    # 3. 代码生成
    try:
        code = generate_code(graph, shapes)
    except Exception as e:
        raise ControllerError(CODE_CODEGEN_FAILED, f"Code generation failed: {e}")

    serializable_shapes = {str(nid): _flatten_shapes(s) for nid, s in shapes.items()}
    return {"code": code, "shapes": serializable_shapes}
