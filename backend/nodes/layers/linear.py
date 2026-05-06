"""线性层节点."""

from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


@register_node("Linear")
class LinearNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Linear",
        category="layer",
        description="Fully connected layer — y = xA^T + b",
        params_schema={
            "in_features": {"type": "int", "default": 784, "required": True, "min": 1},
            "out_features": {"type": "int", "default": 128, "required": True, "min": 1},
            "bias": {"type": "bool", "default": True},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        *prefix, _last = input_shapes[0]
        return [tuple(prefix) + (params["out_features"],)]

    def to_pytorch_init(self, layer_name, params):
        return (
            f"self.{layer_name} = nn.Linear("
            f"{params['in_features']}, {params['out_features']}"
            f"{', bias=False' if params.get('bias') is False else ''})"
        )

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = self.{layer_name}({input_vars[0]})"
