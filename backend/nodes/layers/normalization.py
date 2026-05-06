"""归一化层节点 — BatchNorm, LayerNorm, GroupNorm, RMSNorm."""
from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


@register_node("BatchNorm1d")
class BatchNorm1dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="BatchNorm1d",
        category="layer",
        description="Batch Normalization 1D — normalizes (N, C, L) inputs",
        params_schema={
            "num_features": {"type": "int", "default": 64, "required": True, "min": 1},
            "eps": {"type": "float", "default": 1e-5, "min": 0},
            "momentum": {"type": "float", "default": 0.1, "min": 0, "max": 1},
            "affine": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return (
            f"self.{layer_name} = nn.BatchNorm1d("
            f"{params['num_features']}, eps={params.get('eps', 1e-5)}, "
            f"momentum={params.get('momentum', 0.1)}, "
            f"affine={params.get('affine', True)})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("BatchNorm2d")
class BatchNorm2dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="BatchNorm2d",
        category="layer",
        description="Batch Normalization 2D — normalizes (N, C, H, W) inputs",
        params_schema={
            "num_features": {"type": "int", "default": 64, "required": True, "min": 1},
            "eps": {"type": "float", "default": 1e-5, "min": 0},
            "momentum": {"type": "float", "default": 0.1, "min": 0, "max": 1},
            "affine": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return (
            f"self.{layer_name} = nn.BatchNorm2d("
            f"{params['num_features']}, eps={params.get('eps', 1e-5)}, "
            f"momentum={params.get('momentum', 0.1)}, "
            f"affine={params.get('affine', True)})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("LayerNorm")
class LayerNormNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="LayerNorm",
        category="layer",
        description="Layer Normalization — normalizes over the last D dimensions",
        params_schema={
            "normalized_shape": {"type": "string", "default": "[128]"},
            "eps": {"type": "float", "default": 1e-5, "min": 0},
            "elementwise_affine": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        import ast
        normalized_shape = ast.literal_eval(params.get("normalized_shape", "[128]"))
        return (
            f"self.{layer_name} = nn.LayerNorm("
            f"{normalized_shape}, eps={params.get('eps', 1e-5)}, "
            f"elementwise_affine={params.get('elementwise_affine', True)})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("GroupNorm")
class GroupNormNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="GroupNorm",
        category="layer",
        description="Group Normalization — divides channels into groups and normalizes",
        params_schema={
            "num_groups": {"type": "int", "default": 8, "required": True, "min": 1},
            "num_channels": {"type": "int", "default": 64, "required": True, "min": 1},
            "eps": {"type": "float", "default": 1e-5, "min": 0},
            "affine": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        num_channels = params["num_channels"]
        num_groups = params["num_groups"]
        if num_channels % num_groups != 0:
            raise ValueError(
                f"num_channels ({num_channels}) must be divisible by num_groups ({num_groups})"
            )
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return (
            f"self.{layer_name} = nn.GroupNorm("
            f"{params['num_groups']}, {params['num_channels']}, "
            f"eps={params.get('eps', 1e-5)}, "
            f"affine={params.get('affine', True)})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("RMSNorm")
class RMSNormNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="RMSNorm",
        category="layer",
        description="Root Mean Square Normalization — common in LLaMA-style architectures",
        params_schema={
            "normalized_shape": {"type": "string", "default": "[128]"},
            "eps": {"type": "float", "default": 1e-5, "min": 0},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        import ast
        normalized_shape = ast.literal_eval(params.get("normalized_shape", "[128]"))
        return (
            f"self.{layer_name} = nn.RMSNorm("
            f"{normalized_shape}, eps={params.get('eps', 1e-5)})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"
