"""TorchLab — FastAPI 后端入口 (port 4003).

架构:
  api/routers/    → V (View): 薄 HTTP 层，只做参数提取 + 响应包装
  controllers/    → C (Controller): 业务编排
  core/           → 纯计算引擎
  nodes/          → 节点类型系统（独立模块）
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import nodes  # noqa: F401 — 触发所有 @register_node
from api.routers import nodes as nodes_router
from api.routers import generate as generate_router
from api.routers import custom as custom_router
from api.routers import composite as composite_router
from controllers.composite_controller import load_persisted_composites

load_persisted_composites()

app = FastAPI(title="TorchLab")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nodes_router.router)
app.include_router(generate_router.router)
app.include_router(custom_router.router)
app.include_router(composite_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4003)
