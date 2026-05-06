"""节点元数据路由."""

from fastapi import APIRouter

from api.response import CODE_UNKNOWN, error, ok
from controllers.node_controller import ControllerError, list_all_nodes

router = APIRouter()


@router.get("/api/nodes")
def get_nodes():
    try:
        data = list_all_nodes()
        return ok(data)
    except ControllerError as e:
        return error(e.code, e.msg)
    except Exception as e:
        return error(CODE_UNKNOWN, str(e), http_status=500)
