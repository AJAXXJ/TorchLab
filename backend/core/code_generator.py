"""代码生成器 — 从构建好的图生成 nn.Module 代码."""


def _resolve_var(var_names, nid, port_idx=0):
    """将节点变量名解析为具体端口变量。多输出节点返回元组中的某个元素。"""
    v = var_names[nid]
    if isinstance(v, tuple):
        return v[port_idx]
    return v


def generate_code(graph: dict, shapes: dict | None = None) -> str:
    """根据已构建的图生成 PyTorch nn.Module 代码.

    shapes 参数目前预留，未来可用于在注释中标注 shape。
    """
    node_map = graph["node_map"]
    order = graph["order"]
    input_sources = graph["input_sources"]
    input_nodes = graph["input_nodes"]
    output_nodes = graph["output_nodes"]

    # 为每个节点生成层名和变量名
    var_names: dict[int, str | tuple[str, ...]] = {}
    layer_names: dict[int, str] = {}

    for nid in order:
        nd = node_map[nid]
        outs = nd["instance"].meta.ports.get("outputs", [])
        if len(outs) > 1:
            var_names[nid] = tuple(f"x_{nid}_{i}" for i in range(len(outs)))
        else:
            var_names[nid] = f"x_{nid}"
        if nd["type"] not in ("Input", "Output"):
            layer_names[nid] = f"{nd['type'].lower()}_{nid}"

    # ── __init__ ──
    init_lines: list[str] = [
        "    def __init__(self):",
        "        super().__init__()",
    ]
    for nid in order:
        nd = node_map[nid]
        if nd["type"] in ("Input", "Output"):
            continue
        line = nd["instance"].to_pytorch_init(layer_names[nid], nd["properties"])
        if line.strip():
            for subline in line.split("\n"):
                init_lines.append(f"        {subline}")

    # ── forward ──
    forward_lines: list[str] = []
    forward_params = ", ".join(
        _resolve_var(var_names, nid) for nid in input_nodes
    ) or "x"
    forward_lines.append(f"    def forward(self, {forward_params}):")

    for nid in order:
        nd = node_map[nid]
        if nd["type"] == "Input":
            continue

        in_srcs = input_sources.get(nid, [])
        in_vars = [_resolve_var(var_names, src, src_out_idx)
                   for src, src_out_idx, _ in in_srcs]

        out_v = var_names[nid]
        output_vars = list(out_v) if isinstance(out_v, tuple) else [out_v]

        line = nd["instance"].to_pytorch_forward(
            layer_names.get(nid, ""), in_vars, output_vars, nd["properties"]
        )
        if line.strip():
            for subline in line.split("\n"):
                forward_lines.append(f"        {subline}")

    # return — resolve output node source port indices
    return_var_parts = []
    for onid in output_nodes:
        in_srcs = input_sources.get(onid, [])
        if in_srcs:
            src, src_out_idx, _ = in_srcs[0]
            return_var_parts.append(_resolve_var(var_names, src, src_out_idx))
    if return_var_parts:
        forward_lines.append(f"        return {', '.join(return_var_parts)}")

    # ── 组装 ──
    code = (
        "import torch\n"
        "import torch.nn as nn\n"
        "\n\n"
        "class MyModel(nn.Module):\n"
        + "\n".join(init_lines)
        + "\n\n"
        + "\n".join(forward_lines)
    )
    return code
