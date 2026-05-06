"""卷积层节点 — Conv1d, Conv2d, Conv3d."""
from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


def _conv_out_size(in_size, kernel_size, stride, padding, dilation):
    """计算单个维度的卷积输出尺寸."""
    return (
        in_size + 2 * padding - dilation * (kernel_size - 1) - 1
    ) // stride + 1


@register_node("Conv1d")
class Conv1dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Conv1d",
        category="layer",
        description="1D convolution — for temporal/sequential data (N, C_in, L)",
        params_schema={
            "in_channels": {"type": "int", "default": 3, "required": True, "min": 1},
            "out_channels": {"type": "int", "default": 64, "required": True, "min": 1},
            "kernel_size": {"type": "int", "default": 3, "required": True, "min": 1},
            "stride": {"type": "int", "default": 1, "min": 1},
            "padding": {"type": "int", "default": 0, "min": 0},
            "dilation": {"type": "int", "default": 1, "min": 1},
            "bias": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        N, C_in, L = input_shapes[0]
        L_out = _conv_out_size(
            L, params["kernel_size"], params.get("stride", 1),
            params.get("padding", 0), params.get("dilation", 1),
        )
        return [(N, params["out_channels"], L_out)]

    def to_pytorch_init(self, layer_name, params):
        return (
            f"self.{layer_name} = nn.Conv1d("
            f"{params['in_channels']}, {params['out_channels']}, "
            f"{params['kernel_size']}, stride={params.get('stride', 1)}, "
            f"padding={params.get('padding', 0)}, "
            f"dilation={params.get('dilation', 1)}"
            f"{', bias=False' if params.get('bias') is False else ''})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("Conv2d")
class Conv2dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Conv2d",
        category="layer",
        description="2D convolution — for image data (N, C_in, H, W)",
        params_schema={
            "in_channels": {"type": "int", "default": 3, "required": True, "min": 1},
            "out_channels": {"type": "int", "default": 64, "required": True, "min": 1},
            "kernel_size": {"type": "int", "default": 3, "required": True, "min": 1},
            "stride": {"type": "int", "default": 1, "min": 1},
            "padding": {"type": "int", "default": 0, "min": 0},
            "dilation": {"type": "int", "default": 1, "min": 1},
            "bias": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        N, C_in, H, W = input_shapes[0]
        ks = params["kernel_size"]
        st = params.get("stride", 1)
        pd = params.get("padding", 0)
        di = params.get("dilation", 1)
        H_out = _conv_out_size(H, ks, st, pd, di)
        W_out = _conv_out_size(W, ks, st, pd, di)
        return [(N, params["out_channels"], H_out, W_out)]

    def to_pytorch_init(self, layer_name, params):
        return (
            f"self.{layer_name} = nn.Conv2d("
            f"{params['in_channels']}, {params['out_channels']}, "
            f"{params['kernel_size']}, stride={params.get('stride', 1)}, "
            f"padding={params.get('padding', 0)}, "
            f"dilation={params.get('dilation', 1)}"
            f"{', bias=False' if params.get('bias') is False else ''})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("Conv3d")
class Conv3dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Conv3d",
        category="layer",
        description="3D convolution — for volumetric data (N, C_in, D, H, W)",
        params_schema={
            "in_channels": {"type": "int", "default": 3, "required": True, "min": 1},
            "out_channels": {"type": "int", "default": 64, "required": True, "min": 1},
            "kernel_size": {"type": "int", "default": 3, "required": True, "min": 1},
            "stride": {"type": "int", "default": 1, "min": 1},
            "padding": {"type": "int", "default": 0, "min": 0},
            "dilation": {"type": "int", "default": 1, "min": 1},
            "bias": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        N, C_in, D, H, W = input_shapes[0]
        ks = params["kernel_size"]
        st = params.get("stride", 1)
        pd = params.get("padding", 0)
        di = params.get("dilation", 1)
        D_out = _conv_out_size(D, ks, st, pd, di)
        H_out = _conv_out_size(H, ks, st, pd, di)
        W_out = _conv_out_size(W, ks, st, pd, di)
        return [(N, params["out_channels"], D_out, H_out, W_out)]

    def to_pytorch_init(self, layer_name, params):
        return (
            f"self.{layer_name} = nn.Conv3d("
            f"{params['in_channels']}, {params['out_channels']}, "
            f"{params['kernel_size']}, stride={params.get('stride', 1)}, "
            f"padding={params.get('padding', 0)}, "
            f"dilation={params.get('dilation', 1)}"
            f"{', bias=False' if params.get('bias') is False else ''})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"
