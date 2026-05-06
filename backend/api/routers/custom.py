"""自定义节点管理路由."""

from fastapi import APIRouter

from api.response import CODE_UNKNOWN, error, ok
from api.schemas import CustomNodeRegisterRequest
from controllers.node_controller import ControllerError, register_custom, unregister_custom

router = APIRouter()


@router.post("/api/custom/register")
def register(req: CustomNodeRegisterRequest):
    try:
        data = register_custom(req.code)
        return ok(data, msg=f"Registered {len(data['nodes'])} node(s)")
    except ControllerError as e:
        return error(e.code, e.msg)
    except Exception as e:
        return error(CODE_UNKNOWN, str(e), http_status=500)


@router.delete("/api/custom/{node_type}")
def unregister(node_type: str):
    try:
        unregister_custom(node_type)
        return ok(msg=f"Node '{node_type}' removed")
    except ControllerError as e:
        return error(e.code, e.msg)
    except Exception as e:
        return error(CODE_UNKNOWN, str(e), http_status=500)
