"""Shape 推断引擎 — 按拓扑顺序逐节点推断输出 shape."""

import ast


class ShapeInferError(ValueError):
    """Shape 推断错误."""
    def __init__(self, message: str, node_id: int | None = None):
        self.node_id = node_id
        super().__init__(message)


def infer_shapes(graph: dict) -> dict[int, tuple[tuple[int, ...], ...]]:
    """对已构建的图执行 shape 推断.

    从 Input 节点出发，沿拓扑顺序逐节点调用 infer_output_shape。
    返回 {node_id: (output_shapes, ...)}，每个节点可能有一个或多个输出 shape。
    """
    node_map = graph["node_map"]
    order = graph["order"]
    input_sources = graph["input_sources"]
    shapes: dict[int, tuple[tuple[int, ...], ...]] = {}

    for nid in order:
        nd = node_map[nid]
        instance = nd["instance"]
        params = nd["properties"]

        if nd["type"] == "Input":
            shape_str = params.get("shape", "[784]")
            try:
                shapes[nid] = (tuple(ast.literal_eval(shape_str)),)
            except Exception:
                raise ShapeInferError(
                    f"Invalid shape string: {shape_str}", nid
                )
        else:
            input_srcs = input_sources.get(nid, [])
            # Resolve by source output port index for multi-output upstream nodes
            input_shapes = [shapes[src][src_out_idx] for src, src_out_idx, _ in input_srcs]
            if not input_shapes:
                raise ShapeInferError(
                    f"Node has no input connections", nid
                )
            try:
                shapes[nid] = tuple(instance.infer_output_shape(input_shapes, params))
            except Exception as e:
                raise ShapeInferError(
                    f"Shape inference failed: {e}", nid
                )

    return shapes
