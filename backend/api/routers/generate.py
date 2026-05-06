"""图生成路由."""

from fastapi import APIRouter

from api.response import CODE_UNKNOWN, error, ok
from api.schemas import GenerateRequest
from controllers.generate_controller import ControllerError, execute_generate

router = APIRouter()


@router.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        data = execute_generate(req.nodes, req.links)
        return ok(data)
    except ControllerError as e:
        return error(e.code, e.msg)
    except Exception as e:
        return error(CODE_UNKNOWN, str(e), http_status=500)
