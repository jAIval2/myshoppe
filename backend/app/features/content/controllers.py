from typing import Annotated, Literal
from fastapi import APIRouter, Depends
from app.dependencies import current_actor, get_content
from app.identity import Actor
from app.schemas import CampaignInput
from .interfaces import ContentCommands

router = APIRouter()
Service = Annotated[ContentCommands, Depends(get_content)]
User = Annotated[Actor, Depends(current_actor)]


@router.get("/api/campaigns/{department}")
def campaign(department: Literal["women", "home"], service: Service):
    return service.campaign(department)


@router.get("/api/admin/campaigns/{department}")
def revisions(department: Literal["women", "home"], service: Service, actor: User):
    return service.history(actor, department)


@router.post("/api/admin/campaigns/{department}")
def save(department: Literal["women", "home"], command: CampaignInput, service: Service, actor: User):
    return service.save(actor, department, command)


@router.post("/api/admin/campaign-revisions/{revision_id}/publish")
def publish(revision_id: str, service: Service, actor: User):
    return service.publish(actor, revision_id)
