"""池化层节点 — MaxPool2d, AvgPool2d, AdaptiveAvgPool2d."""
from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


def _pool_out_size(in_size, kernel_size, stride, padding, dilation):
    """计算单个维度的池化输出尺寸."""
    return (
        in_size + 2 * padding - dilation * (kernel_size - 1) - 1
    ) // stride + 1


@register_node("MaxPool2d")
class MaxPool2dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="MaxPool2d",
        category="layer",
        description="2D max pooling — downsamples by taking the maximum in each window",
        params_schema={
            "kernel_size": {"type": "int", "default": 2, "required": True, "min": 1},
            "stride": {"type": "int", "default": 2, "min": 1},
            "padding": {"type": "int", "default": 0, "min": 0},
            "dilation": {"type": "int", "default": 1, "min": 1},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        N, C, H, W = input_shapes[0]
        ks = params["kernel_size"]
        st = params.get("stride", ks)
        pd = params.get("padding", 0)
        di = params.get("dilation", 1)
        H_out = _pool_out_size(H, ks, st, pd, di)
        W_out = _pool_out_size(W, ks, st, pd, di)
        return [(N, C, H_out, W_out)]

    def to_pytorch_init(self, layer_name, params):
        ks = params["kernel_size"]
        return (
            f"self.{layer_name} = nn.MaxPool2d("
            f"{ks}, stride={params.get('stride', ks)}, "
            f"padding={params.get('padding', 0)}, "
            f"dilation={params.get('dilation', 1)})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("AvgPool2d")
class AvgPool2dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="AvgPool2d",
        category="layer",
        description="2D average pooling — downsamples by averaging each window",
        params_schema={
            "kernel_size": {"type": "int", "default": 2, "required": True, "min": 1},
            "stride": {"type": "int", "default": 2, "min": 1},
            "padding": {"type": "int", "default": 0, "min": 0},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        N, C, H, W = input_shapes[0]
        ks = params["kernel_size"]
        st = params.get("stride", ks)
        pd = params.get("padding", 0)
        H_out = _pool_out_size(H, ks, st, pd, 1)
        W_out = _pool_out_size(W, ks, st, pd, 1)
        return [(N, C, H_out, W_out)]

    def to_pytorch_init(self, layer_name, params):
        ks = params["kernel_size"]
        return (
            f"self.{layer_name} = nn.AvgPool2d("
            f"{ks}, stride={params.get('stride', ks)}, "
            f"padding={params.get('padding', 0)})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("AdaptiveAvgPool2d")
class AdaptiveAvgPool2dNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="AdaptiveAvgPool2d",
        category="layer",
        description="2D adaptive average pooling — outputs fixed spatial size regardless of input",
        params_schema={
            "output_size": {"type": "string", "default": "[1, 1]", "description": "Target output size, e.g. [7, 7] or [1, 1]"},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        N, C, H, W = input_shapes[0]
        import ast
        osize = ast.literal_eval(params.get("output_size", "[1, 1]"))
        return [(N, C, osize[0], osize[1])]

    def to_pytorch_init(self, layer_name, params):
        import ast
        osize = ast.literal_eval(params.get("output_size", "[1, 1]"))
        return f"self.{layer_name} = nn.AdaptiveAvgPool2d({osize})"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"
