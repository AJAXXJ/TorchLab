# TorchLab API 接口文档

> 版本：v0.5 · 更新：2026-05-04 · Base URL: `http://localhost:4003`

---

## 一、统一响应格式

所有接口返回格式：

```json
{
  "msg": "string — 人类可读消息",
  "code": "int — 业务状态码, 0 = 成功",
  "data": "object | null — 实际负载"
}
```

### 业务状态码

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1001 | 图构建错误 — 未知节点类型 |
| 1002 | 图构建错误 — 图包含环 |
| 2001 | Shape 推断失败 |
| 2002 | Shape 不兼容 |
| 3001 | 代码生成失败 |
| 4001 | 自定义节点安全检查不通过 |
| 4002 | 自定义节点未继承 ObjectNode |
| 4003 | 不能删除内置节点 |
| 4004 | 自定义节点不存在 |
| 9999 | 未知内部错误 |

---

## 二、接口列表

### 2.1 获取所有节点元数据

```
GET /api/nodes
```

前端启动时调用，获取所有已注册节点（含内置 + 自定义）的元数据，驱动面板渲染和 LiteGraph 节点类动态创建。

**请求：** 无参数

**响应 `data`：**

```json
{
  "nodes": {
    "Linear": {
      "display_name": "Linear",
      "category": "layer",
      "description": "Fully connected layer — y = xA^T + b",
      "is_custom": false,
      "params_schema": {
        "in_features": {
          "type": "int",
          "default": 784,
          "required": true,
          "min": 1
        },
        "out_features": {
          "type": "int",
          "default": 128,
          "required": true,
          "min": 1
        },
        "bias": {
          "type": "bool",
          "default": true
        }
      },
      "ports": {
        "inputs": [
          {
            "id": "in_0",
            "label": "input",
            "dtype": "tensor",
            "required": true
          }
        ],
        "outputs": [
          {
            "id": "out_0",
            "label": "output",
            "dtype": "tensor",
            "required": true
          }
        ]
      }
    }
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `display_name` | string | 前端面板显示名称 |
| `category` | string | 节点分类 (data / layer / activation / control_flow / custom) |
| `description` | string | 节点功能描述 |
| `is_custom` | boolean | 是否为自定义节点 |
| `params_schema` | object | 参数定义，驱动前端动态表单和 LiteGraph widget |
| `params_schema.{key}.type` | string | int / float / bool / string / choice |
| `params_schema.{key}.default` | any | 默认值 |
| `params_schema.{key}.required` | boolean | 是否必填 |
| `params_schema.{key}.min` | number | 最小值 (int/float) |
| `params_schema.{key}.max` | number | 最大值 (int/float) |
| `params_schema.{key}.options` | string[] | 选项列表 (choice) |
| `ports.inputs` | array | 输入端口列表 |
| `ports.outputs` | array | 输出端口列表 |
| `ports.{dir}.id` | string | 端口唯一标识 |
| `ports.{dir}.label` | string | 端口显示名 |
| `ports.{dir}.dtype` | string | 端口数据类型 (tensor / scalar / any) |
| `ports.{dir}.required` | boolean | 是否必连 |

---

### 2.2 生成 PyTorch 代码

```
POST /api/generate
```

接收前端图 JSON（LiteGraph.js 序列化格式），执行 图构建 → Shape 推断 → 代码生成，返回完整 `nn.Module` 代码。

**请求体：**

```json
{
  "nodes": [
    {
      "id": 1,
      "type": "data/Input",
      "pos": [100, 200],
      "properties": { "shape": "784" }
    },
    {
      "id": 2,
      "type": "layer/Linear",
      "pos": [300, 200],
      "properties": { "in_features": 784, "out_features": 128, "bias": true }
    }
  ],
  "links": [
    [1, 1, 0, 2, 0, "tensor"]
  ]
}
```

**请求字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nodes` | array | 节点列表 |
| `nodes[].id` | int | 节点唯一 ID |
| `nodes[].type` | string | LiteGraph 类型路径 (如 `layer/Linear`) |
| `nodes[].pos` | [float, float] | 画布坐标 |
| `nodes[].properties` | object | 节点参数 (key-value，widget 值序列化) |
| `links` | array | 连线列表 |
| `links[]` | array | `[link_id, src_node_id, src_output_slot, tgt_node_id, tgt_input_slot, dtype]` |

**成功响应 `data`：**

```json
{
  "code": "import torch\nimport torch.nn as nn\n\n\nclass MyModel(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.linear_2 = nn.Linear(784, 128)\n\n    def forward(self, x_1):\n        x_2 = self.linear_2(x_1)\n        return x_2",
  "shapes": {
    "1": [784],
    "2": [128]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 完整 `nn.Module` Python 代码 |
| `shapes` | object | `{ node_id: [dim, ...] }` Shape 推断结果 |

**错误响应示例：**

```json
{
  "msg": "Shape inference failed at node #3: Conv2d expects 4D input, got 2D",
  "code": 2001,
  "data": null
}
```

前端在 Inspector 面板中渲染 errors 列表，包含 `node_id` 和 `message`。

---

### 2.3 注册自定义节点

```
POST /api/custom/register
```

上传继承 ObjectNode 的 Python 代码，服务器 AST 安全检查 + importlib 动态加载后注册为可用节点。

**请求体：**

```json
{
  "code": "from nodes.object_node import ObjectNode, ObjectNodeMeta, PortDef\nfrom nodes.registry import register_node\n\n@register_node(\"MyGELU\")\nclass MyGELU(ObjectNode):\n    meta = ObjectNodeMeta(\n        display_name=\"My GELU\",\n        category=\"activation\",\n        description=\"Custom GELU activation\"\n    )\n    ..."
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 完整 Python 源码，必须包含 `@register_node` 装饰的 ObjectNode 子类 |

**安全约束：**

- 禁止调用：`exec` `eval` `compile` `__import__` `open` `globals` `locals`
- 禁止导入：`os` `sys` `subprocess` `shutil` `socket` `pickle` `ctypes` `signal` `atexit`
- 允许导入：`torch` `torch.nn` `torch.nn.functional` 及标准数学库

**成功响应 `data`：**

```json
{
  "nodes": [
    {
      "node_type": "MyGELU",
      "display_name": "My GELU",
      "category": "activation"
    }
  ]
}
```

**错误响应：**

```json
{
  "msg": "Banned import in custom node code: os",
  "code": 4001,
  "data": null
}
```

```json
{
  "msg": "No valid ObjectNode subclass found. Use @register_node decorator and inherit from ObjectNode.",
  "code": 4002,
  "data": null
}
```

---

### 2.4 删除自定义节点

```
DELETE /api/custom/{node_type}
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `node_type` | string | 节点类型名（如 `MyGELU`） |

**约束：**

- 内置节点 (`Input` `Output` `Linear` `ReLU` `Sigmoid`) 不可删除
- 不存在的节点类型返回 4004

**成功响应 `data`：**

```json
null
```

**错误响应：**

```json
{
  "msg": "Cannot remove built-in node type",
  "code": 4003,
  "data": null
}
```

---

## 三、前端集成指南

### 3.1 启动流程

```
1. GET /api/nodes → 获取所有节点元数据 (useNodeRegistry.fetchNodes)
2. litegraph-factory.ts 遍历 metas，为每个节点类型动态创建 LiteGraph 节点类:
   - meta.ports.inputs → this.addInput(label, dtype)
   - meta.ports.outputs → this.addOutput(label, dtype)
   - meta.params_schema → this.addWidget(type, key, default, ...)
   - 节点最小宽度设为 210px，防止 widget 值与 pin 角标重叠
3. LiteGraph.registerNodeType(`category/type`, DynamicNodeClass)
4. NodePalette (悬浮左侧面板) 按 category 分组展示，支持点击和拖拽添加
5. LiteGraph 内置 ContextMenu / prompt / showSearchBox 全部禁用，
   由 Vue Teleport 自定义右键菜单和 InspectorPanel 替代
```

### 3.2 生成流程

```
1. 用户点击 "Generate Code" (AppHeader)
2. canvasRef.getGraphData() → LiteGraph 序列化为 { nodes, links }
3. POST /api/generate { nodes, links }
4. 成功: showCode = true → Inspector (悬浮右侧面板) 自动展开展示 code
5. 失败: Inspector 渲染 errors 列表 (红色错误卡片，含 node_id 定位)
```

### 3.3 自定义节点流程

```
1. 用户编写 Python 代码 (继承 ObjectNode + @register_node)
2. POST /api/custom/register { code }
3. 成功后: 再次 fetchNodes() 刷新面板
4. 新节点自动出现在 custom 分类下
```

### 3.4 LiteGraph.js 类型路径约定

节点在 LiteGraph 中的注册类型格式为 `category/type_name`：

| 后端 type | LiteGraph 类型路径 | 分类 |
|-----------|-------------------|------|
| Input | `data/Input` | data |
| Output | `data/Output` | data |
| Linear | `layer/Linear` | layer |
| Conv1d | `layer/Conv1d` | layer |
| Conv2d | `layer/Conv2d` | layer |
| Conv3d | `layer/Conv3d` | layer |
| BatchNorm1d | `layer/BatchNorm1d` | layer |
| BatchNorm2d | `layer/BatchNorm2d` | layer |
| LayerNorm | `layer/LayerNorm` | layer |
| GroupNorm | `layer/GroupNorm` | layer |
| RMSNorm | `layer/RMSNorm` | layer |
| MaxPool2d | `layer/MaxPool2d` | layer |
| AvgPool2d | `layer/AvgPool2d` | layer |
| AdaptiveAvgPool2d | `layer/AdaptiveAvgPool2d` | layer |
| Dropout | `layer/Dropout` | layer |
| AlphaDropout | `layer/AlphaDropout` | layer |
| Embedding | `layer/Embedding` | layer |
| ReLU | `activation/ReLU` | activation |
| Sigmoid | `activation/Sigmoid` | activation |
| GELU | `activation/GELU` | activation |
| SiLU | `activation/SiLU` | activation |
| Tanh | `activation/Tanh` | activation |
| Softmax | `activation/Softmax` | activation |
| Add | `control_flow/Add` | control_flow |
| Concat | `control_flow/Concat` | control_flow |
| Split | `control_flow/Split` | control_flow |
| Reshape | `control_flow/Reshape` | control_flow |
| Permute | `control_flow/Permute` | control_flow |
| Squeeze | `control_flow/Squeeze` | control_flow |
| Unsqueeze | `control_flow/Unsqueeze` | control_flow |

自定义节点以其注册名作为 type，前端自动归入 `custom` 分类。

---

## 四、后端架构

```
                              main.py (FastAPI, port 4003)
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    api/routers/nodes.py    api/routers/generate.py  api/routers/custom.py
    (GET /api/nodes)        (POST /api/generate)     (POST|DELETE /api/custom/*)
            │                       │                       │
            ▼                       ▼                       ▼
    controllers/              controllers/             controllers/
    node_controller.py        generate_controller.py   node_controller.py
            │                       │                       │
            ▼               ┌───────┴───────┐               ▼
    nodes/registry.py       ▼               ▼        importlib + AST
    nodes/object_node.py  core/            core/      custom_nodes/
    nodes/data_nodes.py   graph_builder.py code_generator.py
    nodes/layers/*        shape_inferrer.py

    V (View)      → 薄 HTTP 层，参数提取 + 响应包装
    C (Controller) → 业务编排，异常 → 业务状态码
    Core          → 纯函数引擎，零 HTTP 依赖
    Nodes         → 独立模块，ObjectNode ABC + 注册表
```

---

*文档维护：项目核心团队 · 接口变更请同步更新*
