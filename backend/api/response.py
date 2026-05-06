"""统一 API 响应封装.

所有接口返回格式: { msg: str, code: int, data: T | null }
  - code 0      → 成功
  - code 1xxx   → 图构建错误
  - code 2xxx   → Shape 推断错误
  - code 3xxx   → 代码生成错误
  - code 4xxx   → 自定义节点错误
  - code 9999   → 未知错误
"""

from typing import Any

from fastapi.responses import JSONResponse

# ── 业务状态码 ───────────────────────────────────────────────────

CODE_OK = 0

# 图构建
CODE_UNKNOWN_NODE_TYPE = 1001
CODE_GRAPH_CYCLE = 1002

# Shape 推断
CODE_SHAPE_INFER_FAILED = 2001
CODE_SHAPE_INCOMPATIBLE = 2002

# 代码生成
CODE_CODEGEN_FAILED = 3001

# 自定义节点
CODE_CUSTOM_SAFETY_BANNED = 4001
CODE_CUSTOM_NOT_OBJECTNODE = 4002
CODE_CUSTOM_CANNOT_REMOVE_BUILTIN = 4003
CODE_CUSTOM_NOT_FOUND = 4004

# 未知
CODE_UNKNOWN = 9999


# ── 辅助函数 ────────────────────────────────────────────────────


def ok(data: Any = None, msg: str = "ok") -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"msg": msg, "code": CODE_OK, "data": data},
    )


def error(code: int, msg: str, http_status: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"msg": msg, "code": code, "data": None},
    )
