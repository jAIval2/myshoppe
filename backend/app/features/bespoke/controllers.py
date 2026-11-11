from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, Response
from app.dependencies import current_actor, ensure_actor, get_bespoke
from app.identity import Actor
from .interfaces import Bespoke
from .schemas import Save, Action

router = APIRouter()
Service = Annotated[Bespoke, Depends(get_bespoke)]
User = Annotated[Actor, Depends(current_actor)]
Writer = Annotated[Actor, Depends(ensure_actor)]


@router.get("/api/bespoke")
def designs(service: Service, actor: User):
    return service.list(actor)


@router.post("/api/bespoke")
def create(service: Service, actor: Writer):
    return service.create(actor)


@router.get("/api/bespoke/{design_id}")
def design(design_id: UUID, service: Service, actor: User):
    return service.get(actor, str(design_id))


@router.put("/api/bespoke/{design_id}")
def save(design_id: UUID, command: Save, service: Service, actor: Writer):
    return service.save(actor, str(design_id), command)


@router.post("/api/bespoke/{design_id}/actions")
def action(design_id: UUID, command: Action, service: Service, actor: Writer):
    return service.action(actor, str(design_id), command)


@router.post("/api/bespoke/{design_id}/assets")
async def upload(design_id: UUID, file: UploadFile, service: Service, actor: Writer):
    from starlette.concurrency import run_in_threadpool

    data = await file.read(5_000_001)
    return await run_in_threadpool(service.upload, actor, str(design_id), data, file.content_type or "")


@router.get("/api/bespoke-assets/{asset_id}")
def asset(asset_id: UUID, service: Service, actor: User):
    value = service.asset(actor, str(asset_id))
    return Response(
        value["data"], media_type=value["content_type"], headers={"Cache-Control": "private, no-store"}
    )


@router.get("/api/admin/bespoke")
def admin_list(service: Service, actor: User):
    return service.list(actor, True)


@router.get("/api/admin/bespoke/{design_id}")
def admin_design(design_id: UUID, service: Service, actor: User):
    return service.get(actor, str(design_id), True)


@router.post("/api/admin/bespoke/{design_id}/actions")
def review(design_id: UUID, command: Action, service: Service, actor: User):
    return service.action(actor, str(design_id), command, True)
