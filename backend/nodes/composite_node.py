"""Composite node — 子图组合节点.

CompositeNode 是动态创建的类型化子图包装器.
每个组合节点存储其内部子图并在 to_pytorch_* 方法中展开.
"""
import json
from collections import defaultdict, deque
from .object_node import ObjectNode, ObjectNodeMeta, PortDef


class CompositeNode(ObjectNode):
    """子图组合节点基类.

    子类设置类级属性 _subgraph_json, _display_name, _input_ports, _output_ports.
    meta 在首次访问时从这些属性动态构建.
    """

    # The following are set by subclasses / dynamic creation.
    # meta is set as a class attribute (not @property) so get_all_meta() works.
    meta: ObjectNodeMeta = ObjectNodeMeta(
        display_name="Composite",
        category="custom",
        description="Composite node",
    )
    _subgraph_json: str = "{}"

    def _subgraph(self) -> dict:
        return json.loads(self._subgraph_json)

    # ── ObjectNode interface ──────────────────────────────────────

    def infer_output_shape(self, input_shapes, params):
        from core.graph_builder import build_graph
        from core.shape_inferrer import infer_shapes

        sub = self._subgraph()
        # Store input shapes into Input nodes' properties
        inp_idx = 0
        for n in sub["nodes"]:
            if n["type"] in ("Input", "data/Input"):
                if inp_idx < len(input_shapes):
                    n["properties"]["shape"] = str(list(input_shapes[inp_idx]))
                    inp_idx += 1

        g = build_graph(sub["nodes"], sub["links"])
        shapes = infer_shapes(g)
        output_nodes = g["output_nodes"]
        result = []
        for onid in output_nodes:
            in_srcs = g["input_sources"].get(onid, [])
            if in_srcs:
                src, src_out_idx, _ = in_srcs[0]
                result.append(shapes[src][src_out_idx])
        return result

    def to_pytorch_init(self, layer_name, params):
        sub = self._subgraph()
        g = _build(sub)
        return _gen_init(g, layer_name)

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        sub = self._subgraph()
        g = _build(sub)
        return _gen_forward(g, input_vars, output_vars, layer_name)


# ── 辅助函数 ──────────────────────────────────────────────────────


def _build(sub: dict) -> dict:
    """轻量级子图构建."""
    from nodes.registry import get_node_class

    node_map: dict[int, dict] = {}
    for n in sub["nodes"]:
        raw_type = n["type"]
        simple_type = raw_type.rsplit("/", 1)[-1]
        cls = get_node_class(simple_type)
        node_map[n["id"]] = {
            "id": n["id"], "type": simple_type,
            "instance": cls(),
            "properties": n.get("properties", {}),
        }

    adj: dict[int, list[int]] = defaultdict(list)
    input_sources: dict[int, list[tuple[int, int, int]]] = defaultdict(list)

    for link in sub["links"]:
        _, src_id, src_out_idx, tgt_id, tgt_in_idx, _ = link
        adj[src_id].append(tgt_id)
        input_sources[tgt_id].append((src_id, src_out_idx, tgt_in_idx))

    for tgt_id in input_sources:
        input_sources[tgt_id].sort(key=lambda x: x[2])

    # Kahn topological sort
    in_degree = {nid: 0 for nid in node_map}
    for src, targets in adj.items():
        for tgt in targets:
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    order: list[int] = []
    while queue:
        nid = queue.popleft()
        order.append(nid)
        for tgt in adj.get(nid, []):
            in_degree[tgt] -= 1
            if in_degree[tgt] == 0:
                queue.append(tgt)

    input_nodes = [nid for nid, nd in node_map.items() if nd["type"] == "Input"]
    output_nodes = [nid for nid, nd in node_map.items() if nd["type"] == "Output"]

    return {
        "node_map": node_map, "adj": dict(adj),
        "input_sources": dict(input_sources), "order": order,
        "input_nodes": input_nodes, "output_nodes": output_nodes,
    }


def _resolve_var(var_names: dict, nid: int, port_idx: int = 0):
    v = var_names[nid]
    if isinstance(v, tuple):
        return v[port_idx]
    return v


def _gen_init(graph: dict, prefix: str) -> str:
    """为子图生成 __init__ 行 (每行已是完整语句, 由调用方缩进)."""
    node_map = graph["node_map"]
    order = graph["order"]
    lines: list[str] = []
    for nid in order:
        nd = node_map[nid]
        if nd["type"] in ("Input", "Output"):
            continue
        layer_name = f"{prefix}_{nd['type'].lower()}_{nid}"
        line = nd["instance"].to_pytorch_init(layer_name, nd["properties"])
        if line.strip():
            lines.append(line)
    return "\n".join(lines)


def _gen_forward(graph: dict, input_vars: list[str],
                 output_vars: list[str], prefix: str) -> str:
    """为子图生成 forward 行."""
    node_map = graph["node_map"]
    order = graph["order"]
    input_sources = graph["input_sources"]
    input_nodes = graph["input_nodes"]
    output_nodes = graph["output_nodes"]

    # Build variable names and layer names
    var_names: dict[int, str | tuple[str, ...]] = {}
    layer_names: dict[int, str] = {}
    # Use prefix to scope internal vars and avoid collision with outer graph
    vprefix = f"c_{prefix}"

    for nid in order:
        nd = node_map[nid]
        outs = nd["instance"].meta.ports.get("outputs", [])
        if len(outs) > 1:
            var_names[nid] = tuple(f"{vprefix}_{nid}_{i}" for i in range(len(outs)))
        else:
            var_names[nid] = f"{vprefix}_{nid}"
        if nd["type"] not in ("Input", "Output"):
            layer_names[nid] = f"{prefix}_{nd['type'].lower()}_{nid}"

    # Map composite input vars → subgraph Input node var names
    for i, in_nid in enumerate(input_nodes):
        if i < len(input_vars):
            var_names[in_nid] = input_vars[i]

    lines: list[str] = []
    for nid in order:
        nd = node_map[nid]
        if nd["type"] in ("Input", "Output"):
            continue

        in_srcs = input_sources.get(nid, [])
        in_vars = [_resolve_var(var_names, src, src_out_idx)
                   for src, src_out_idx, _ in in_srcs]

        out_v = var_names[nid]
        out_list = list(out_v) if isinstance(out_v, tuple) else [out_v]

        line = nd["instance"].to_pytorch_forward(
            layer_names[nid], in_vars, out_list, nd["properties"]
        )
        if line.strip():
            lines.append(line)

    # Map Output nodes → composite output variables
    for i, onid in enumerate(output_nodes):
        in_srcs = input_sources.get(onid, [])
        if in_srcs and i < len(output_vars):
            src, src_out_idx, _ = in_srcs[0]
            var = _resolve_var(var_names, src, src_out_idx)
            lines.append(f"{output_vars[i]} = {var}")

    return "\n".join(lines)
