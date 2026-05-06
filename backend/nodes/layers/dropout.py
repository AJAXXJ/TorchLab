"""Dropout 节点."""
from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


@register_node("Dropout")
class DropoutNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Dropout",
        category="layer",
        description="Dropout — randomly zeroes elements during training with probability p",
        params_schema={
            "p": {"type": "float", "default": 0.5, "min": 0, "max": 1},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return f"self.{layer_name} = nn.Dropout(p={params.get('p', 0.5)})"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"


@register_node("AlphaDropout")
class AlphaDropoutNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="AlphaDropout",
        category="layer",
        description="AlphaDropout — preserves mean and variance, for SELU activations",
        params_schema={
            "p": {"type": "float", "default": 0.5, "min": 0, "max": 1},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return f"self.{layer_name} = nn.AlphaDropout(p={params.get('p', 0.5)})"

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"
