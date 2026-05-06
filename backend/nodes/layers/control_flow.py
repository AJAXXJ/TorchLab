"""控制流节点 — Add, Concat, Split, Reshape, Permute, Squeeze, Unsqueeze."""
import ast
from ..object_node import ObjectNode, ObjectNodeMeta, PortDef
from ..registry import register_node


@register_node("Add")
class AddNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Add",
        category="control_flow",
        description="Element-wise addition with broadcasting — supports skip/residual connections",
        params_schema={},
        ports={
            "inputs": [
                PortDef(id="in_0", label="input_a"),
                PortDef(id="in_1", label="input_b"),
            ],
            "outputs": [
                PortDef(id="out_0", label="output"),
            ],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        s1, s2 = input_shapes[0], input_shapes[1]
        max_len = max(len(s1), len(s2))
        s1 = (1,) * (max_len - len(s1)) + s1
        s2 = (1,) * (max_len - len(s2)) + s2
        result = tuple(max(a, b) for a, b in zip(s1, s2))
        # Broadcast compatibility check
        for a, b in zip(s1, s2):
            if a != 1 and b != 1 and a != b:
                raise ValueError(
                    f"Incompatible shapes for Add: {input_shapes[0]} vs {input_shapes[1]}"
                )
        return [result]

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = {' + '.join(input_vars)}"


@register_node("Concat")
class ConcatNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Concat",
        category="control_flow",
        description="Concatenate tensors along a dimension",
        params_schema={
            "dim": {"type": "int", "default": 1, "required": True, "min": 0},
        },
        ports={
            "inputs": [
                PortDef(id="in_0", label="input_a"),
                PortDef(id="in_1", label="input_b"),
            ],
            "outputs": [
                PortDef(id="out_0", label="output"),
            ],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        dim = params.get("dim", 1)
        s1, s2 = input_shapes[0], input_shapes[1]
        if len(s1) != len(s2):
            raise ValueError(
                f"Concat requires same number of dimensions, got {len(s1)} vs {len(s2)}"
            )
        result = list(s1)
        result[dim] = s1[dim] + s2[dim]
        # Verify other dimensions match
        for i in range(len(s1)):
            if i != dim and s1[i] != s2[i]:
                raise ValueError(
                    f"Concat dimension mismatch at dim {i}: {s1[i]} vs {s2[i]}"
                )
        return [tuple(result)]

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        vars_str = ", ".join(input_vars)
        return f"{output_vars[0]} = torch.cat([{vars_str}], dim={params.get('dim', 1)})"


@register_node("Split")
class SplitNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Split",
        category="control_flow",
        description="Split tensor into two parts along a dimension (equal halves)",
        params_schema={
            "dim": {"type": "int", "default": 1, "required": True, "min": 0},
        },
        ports={
            "inputs": [
                PortDef(id="in_0", label="input"),
            ],
            "outputs": [
                PortDef(id="out_0", label="output_a"),
                PortDef(id="out_1", label="output_b"),
            ],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        dim = params.get("dim", 1)
        s = list(input_shapes[0])
        if s[dim] % 2 != 0:
            raise ValueError(
                f"Split dimension {dim} must be even, got {s[dim]}"
            )
        half = s[dim] // 2
        s1 = list(s)
        s1[dim] = half
        s2 = list(s)
        s2[dim] = half
        return [tuple(s1), tuple(s2)]

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return (
            f"{output_vars[0]}, {output_vars[1]} = "
            f"torch.chunk({input_vars[0]}, 2, dim={params.get('dim', 1)})"
        )


@register_node("Reshape")
class ReshapeNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Reshape",
        category="control_flow",
        description="Reshape tensor to a target shape — use -1 to infer one dimension automatically",
        params_schema={
            "shape": {"type": "string", "default": "[1, -1]", "description": "Target shape, e.g. [B, -1] or [1, 28, 28]"},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        target = ast.literal_eval(params["shape"])
        inp = input_shapes[0]
        inp_elems = 1
        for d in inp:
            inp_elems *= d
        known_elems = 1
        neg_idx = -1
        for i, d in enumerate(target):
            if d == -1:
                if neg_idx >= 0:
                    raise ValueError("Only one dimension can be -1")
                neg_idx = i
            else:
                known_elems *= d
        if neg_idx >= 0:
            inferred = inp_elems // known_elems
            if inp_elems % known_elems != 0:
                raise ValueError(
                    f"Cannot reshape {inp} to {target}: total elements {inp_elems} not divisible by {known_elems}"
                )
            result = list(target)
            result[neg_idx] = inferred
            return [tuple(result)]
        if known_elems != inp_elems:
            raise ValueError(
                f"Cannot reshape {inp} to {target}: element count mismatch {inp_elems} vs {known_elems}"
            )
        return [tuple(target)]

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        shape = params.get("shape", "[1, -1]")
        return f"{output_vars[0]} = torch.reshape({input_vars[0]}, {shape})"


@register_node("Permute")
class PermuteNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Permute",
        category="control_flow",
        description="Permute tensor dimensions — reorder axes",
        params_schema={
            "dims": {"type": "string", "default": "[1, 0]", "description": "New axis order, e.g. [1, 0] to swap first two dims"},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        dims = ast.literal_eval(params["dims"])
        inp = input_shapes[0]
        if len(dims) != len(inp):
            raise ValueError(
                f"Permute dims count {len(dims)} must match input ndim {len(inp)}"
            )
        return [tuple(inp[d] for d in dims)]

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        dims = params.get("dims", "[1, 0]")
        return f"{output_vars[0]} = {input_vars[0]}.permute({dims})"


@register_node("Squeeze")
class SqueezeNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Squeeze",
        category="control_flow",
        description="Remove dimensions of size 1 — optionally target a specific dimension",
        params_schema={
            "dim": {"type": "int", "default": -1, "min": -1, "description": "Dimension to squeeze, or -1 to remove all size-1 dims"},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        dim = params.get("dim", -1)
        inp = list(input_shapes[0])
        if dim == -1:
            result = [d for d in inp if d != 1]
            if not result:
                result = [1]
            return [tuple(result)]
        if dim < 0:
            dim = len(inp) + dim
        if dim < 0 or dim >= len(inp):
            raise ValueError(f"Squeeze dim {params.get('dim')} out of range for shape {inp}")
        if inp[dim] != 1:
            raise ValueError(f"Squeeze dim {params.get('dim')} has size {inp[dim]}, expected 1")
        inp.pop(dim)
        return [tuple(inp)]

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        dim = params.get("dim", -1)
        if dim == -1:
            return f"{output_vars[0]} = torch.squeeze({input_vars[0]})"
        return f"{output_vars[0]} = torch.squeeze({input_vars[0]}, dim={dim})"


@register_node("Unsqueeze")
class UnsqueezeNode(ObjectNode):
    meta = ObjectNodeMeta(
        display_name="Unsqueeze",
        category="control_flow",
        description="Add a dimension of size 1 at the specified position",
        params_schema={
            "dim": {"type": "int", "default": 0, "required": True, "min": -5, "max": 5},
        },
        ports={
            "inputs": [PortDef(id="in_0", label="input")],
            "outputs": [PortDef(id="out_0", label="output")],
        },
    )

    def infer_output_shape(self, input_shapes, params):
        dim = params["dim"]
        inp = list(input_shapes[0])
        if dim < 0:
            dim = len(inp) + 1 + dim
        if dim < 0 or dim > len(inp):
            raise ValueError(f"Unsqueeze dim {params['dim']} out of range for shape {inp}")
        inp.insert(dim, 1)
        return [tuple(inp)]

    def to_pytorch_init(self, layer_name, params):
        return ""

    def to_pytorch_forward(self, layer_name, input_vars, output_vars, params):
        return f"{output_vars[0]} = {input_vars[0]}.unsqueeze(dim={params['dim']})"
