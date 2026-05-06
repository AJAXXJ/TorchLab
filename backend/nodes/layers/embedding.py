"""嵌入层节点 — Embedding."""
from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


@register_node("Embedding")
class EmbeddingNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Embedding",
        category="layer",
        description="Lookup embedding — maps integer indices to dense vectors (N, L) → (N, L, E)",
        params_schema={
            "num_embeddings": {"type": "int", "default": 10000, "required": True, "min": 1},
            "embedding_dim": {"type": "int", "default": 128, "required": True, "min": 1},
            "padding_idx": {"type": "int", "default": -1, "min": -1, "description": "Padding token index, -1 for none"},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="indices", dtype="scalar")],
            "outputs": [PortDef(id="out_0", label="embeddings", dtype="tensor")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        inp = input_shapes[0]
        return [tuple(inp) + (params["embedding_dim"],)]

    def to_pytorch_init(self, layer_name, params):
        padding_idx = params.get("padding_idx", -1)
        if padding_idx >= 0:
            return (
                f"self.{layer_name} = nn.Embedding("
                f"{params['num_embeddings']}, {params['embedding_dim']}, "
                f"padding_idx={padding_idx})"
            )
        return (
            f"self.{layer_name} = nn.Embedding("
            f"{params['num_embeddings']}, {params['embedding_dim']})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"
