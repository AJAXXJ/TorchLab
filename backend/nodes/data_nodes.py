"""数据输入/输出节点."""

from .object_node import ObjectNode, ObjectNodeMeta, PortDef
from .registry import register_node


@register_node("Input")
class InputNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Input",
        category="data",
        description="Data input node — defines model input shape",
        params_schema={
            "shape": {
                "type": "string",
                "default": "[784]",
                "description": "Input tensor shape, e.g. [784] or [3,224,224]",
            }
        },
        ports={
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        import ast
        return [tuple(ast.literal_eval(params["shape"]))]

    def to_pytorch_init(self, layer_name, params):
        return ""  # Input 不需要在 __init__ 中实例化

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return ""  # Input 由 forward 参数直接提供


@register_node("Output")
class OutputNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Output",
        category="data",
        description="Model output node",
        params_schema={},
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        return input_shapes

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = {input_vars[0]}"
