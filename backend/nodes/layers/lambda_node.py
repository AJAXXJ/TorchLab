"""Lambda 节点 — 函数式自定义表达式，支持多输入多输出."""
import re
from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


@register_node("Lambda")
class LambdaNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Lambda",
        category="control_flow",
        description="Inline Python expression — supports multi-input (x0..x3) and tuple output",
        params_schema={
            "expression": {
                "type": "string",
                "default": "x0",
                "description": "Expression. Use x0..x3 for inputs. Comma for tuple output: e.g. x0*2, x0+1",
            },
            "imports": {
                "type": "string",
                "default": "",
                "description": "Extra imports, e.g. import torch.nn.functional as F",
            },
        },
        ports={
            "inputs": [
                PortDef(id="in_0", label="x0"),
                PortDef(id="in_1", label="x1"),
                PortDef(id="in_2", label="x2"),
                PortDef(id="in_3", label="x3"),
            ],
            "outputs": [
                PortDef(id="out_0", label="out_0"),
                PortDef(id="out_1", label="out_1"),
                PortDef(id="out_2", label="out_2"),
            ],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        # Passthrough first input shape for all outputs
        s = input_shapes[0]
        outs = self.meta.ports.get("outputs", [])
        return [s] * len(outs)

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        expr = params["expression"]
        imports = params.get("imports", "").strip()

        # Replace input variable references
        for i, v in enumerate(input_vars):
            expr = re.sub(r"\bx" + str(i) + r"\b", v, expr)
        # Backward compat: plain "x" for single input
        if len(input_vars) == 1:
            expr = re.sub(r"\bx\b", input_vars[0], expr)

        lines: list[str] = []
        if imports:
            lines.append(imports)

        # Count top-level commas to determine output arity
        depth = 0
        commas = 0
        for ch in expr:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                commas += 1
        used_outputs = output_vars[: commas + 1]

        if len(used_outputs) > 1:
            lines.append(f"{', '.join(used_outputs)} = {expr}")
        else:
            lines.append(f"{used_outputs[0]} = {expr}")
        return "\n".join(lines)
