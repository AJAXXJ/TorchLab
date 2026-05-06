"""激活函数节点."""

from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


@register_node("ReLU")
class ReLUNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="ReLU",
        category="activation",
        description="Rectified Linear Unit — max(0, x)",
        params_schema={
            "inplace": {"type": "bool", "default": False},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        inplace = params.get("inplace", False)
        return f"self.{layer_name} = nn.ReLU(inplace={inplace})"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("Sigmoid")
class SigmoidNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Sigmoid",
        category="activation",
        description="Sigmoid function — 1 / (1 + exp(-x))",
        params_schema={},
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return f"self.{layer_name} = nn.Sigmoid()"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("GELU")
class GELUNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="GELU",
        category="activation",
        description="Gaussian Error Linear Unit — x * Phi(x)",
        params_schema={},
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return f"self.{layer_name} = nn.GELU()"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("SiLU")
class SiLUNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="SiLU",
        category="activation",
        description="Sigmoid Linear Unit — x * sigmoid(x), also known as Swish",
        params_schema={},
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return f"self.{layer_name} = nn.SiLU()"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("Tanh")
class TanhNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Tanh",
        category="activation",
        description="Hyperbolic tangent — (exp(x) - exp(-x)) / (exp(x) + exp(-x))",
        params_schema={},
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return f"self.{layer_name} = nn.Tanh()"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("Softmax")
class SoftmaxNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Softmax",
        category="activation",
        description="Softmax — exp(x_i) / sum(exp(x_j)) along a dimension",
        params_schema={
            "dim": {"type": "int", "default": -1, "min": -5, "max": 5},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return f"self.{layer_name} = nn.Softmax(dim={params.get('dim', -1)})"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"
