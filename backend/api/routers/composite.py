"""Composite node API router."""
from fastapi import APIRouter

from api.response import ok, error, CODE_UNKNOWN
from api.schemas import CompositeCreateRequest
from controllers.composite_controller import create_composite, remove_composite
from controllers.node_controller import ControllerError

router = APIRouter()


@router.post("/api/composite/create")
def create(req: CompositeCreateRequest):
    try:
        data = create_composite(
            name=req.name,
            subgraph={"nodes": req.subgraph_nodes, "links": req.subgraph_links},
            external_inputs=req.external_inputs,
            external_outputs=req.external_outputs,
        )
        return ok({"node": data}, msg=f"Created composite node '{req.name}'")
    except ControllerError as e:
        return error(e.code, e.msg)
    except Exception as e:
        return error(CODE_UNKNOWN, str(e), http_status=500)


@router.delete("/api/composite/{name}")
def remove(name: str):
    try:
        remove_composite(name)
        return ok(msg=f"Removed composite node '{name}'")
    except ControllerError as e:
        return error(e.code, e.msg)
    except Exception as e:
        return error(CODE_UNKNOWN, str(e), http_status=500)
