"""图构建器 — JSON 图数据 → 内部表示 (node 实例 + 邻接表 + 拓扑排序)."""

from collections import defaultdict, deque

from nodes.registry import get_node_class


class GraphBuildError(ValueError):
    """图构建错误."""
    def __init__(self, message: str, node_id: int | None = None):
        self.node_id = node_id
        super().__init__(message)


def build_graph(nodes: list[dict], links: list[list]) -> dict:
    """将前端 JSON 图解析为内部表示.

    返回:
      {
        "node_map": {id: {id, type, cls, instance, properties}},
        "adj": {src_id: [tgt_id, ...]},
        "input_sources": {tgt_id: [(src_id, src_port_idx, tgt_port_idx), ...]},
        "order": [id, ...]  (拓扑顺序),
        "input_nodes": [id, ...],
        "output_nodes": [id, ...],
      }
    """
    # 1. 解析节点
    node_map: dict[int, dict] = {}
    for n in nodes:
        raw_type = n["type"]
        simple_type = raw_type.rsplit("/", 1)[-1]
        cls = get_node_class(simple_type)
        if cls is None:
            raise GraphBuildError(f"Unknown node type: {simple_type}", n["id"])
        instance = cls()
        node_map[n["id"]] = {
            "id": n["id"],
            "type": simple_type,
            "cls": cls,
            "instance": instance,
            "properties": n.get("properties", {}),
        }

    # 2. 解析边 → 邻接表 + 输入映射
    adj: dict[int, list[int]] = defaultdict(list)
    input_sources: dict[int, list[tuple[int, int, int]]] = defaultdict(list)

    for link in links:
        _, src_id, src_out_idx, tgt_id, tgt_in_idx, _ = link
        adj[src_id].append(tgt_id)
        input_sources[tgt_id].append((src_id, src_out_idx, tgt_in_idx))

    for tgt_id in input_sources:
        input_sources[tgt_id].sort(key=lambda x: x[2])

    # 3. 拓扑排序
    order = _topo_sort(list(node_map), adj)

    # 4. 分类
    input_nodes = [nid for nid, nd in node_map.items() if nd["type"] == "Input"]
    output_nodes = [nid for nid, nd in node_map.items() if nd["type"] == "Output"]

    return {
        "node_map": node_map,
        "adj": dict(adj),
        "input_sources": dict(input_sources),
        "order": order,
        "input_nodes": input_nodes,
        "output_nodes": output_nodes,
    }


def _topo_sort(node_ids: list[int], adj: dict[int, list[int]]) -> list[int]:
    """Kahn 拓扑排序."""
    in_degree = {nid: 0 for nid in node_ids}
    for src, targets in adj.items():
        for tgt in targets:
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    result = []
    while queue:
        nid = queue.popleft()
        result.append(nid)
        for tgt in adj.get(nid, []):
            in_degree[tgt] -= 1
            if in_degree[tgt] == 0:
                queue.append(tgt)

    if len(result) != len(node_ids):
        raise GraphBuildError("Graph contains a cycle")
    return result
