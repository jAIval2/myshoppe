from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import current_actor, get_orders
from app.identity import Actor
from app.schemas import RefundInput, ShipmentInput, ReturnInput, Command
from .interfaces import OrderCommands

router = APIRouter()
Service = Annotated[OrderCommands, Depends(get_orders)]
User = Annotated[Actor, Depends(current_actor)]


@router.get("/api/orders")
def orders(service: Service, actor: User):
    return service.list(actor)


@router.get("/api/orders/{order_id}")
def order(order_id: str, service: Service, actor: User):
    return service.get(actor, order_id)


@router.post("/api/orders/{order_id}/returns")
def request_return(order_id: str, command: ReturnInput, service: Service, actor: User):
    return service.request_return(actor, order_id, command)


@router.get("/api/admin/dashboard")
def dashboard(service: Service, actor: User):
    return service.dashboard(actor)


@router.get("/api/admin/orders")
def admin_orders(service: Service, actor: User):
    return service.list(actor, True)


@router.get("/api/admin/orders/{order_id}")
def admin_order(order_id: str, service: Service, actor: User):
    return service.get(actor, order_id, True)


@router.post("/api/admin/orders/{order_id}/refunds")
def refund(order_id: str, command: RefundInput, service: Service, actor: User):
    return service.refund(actor, order_id, command)


@router.post("/api/admin/orders/{order_id}/shipments")
def ship(order_id: str, command: ShipmentInput, service: Service, actor: User):
    return service.ship(actor, order_id, command)


@router.post("/api/admin/orders/{order_id}/delivered")
def delivered(order_id: str, service: Service, actor: User):
    return service.deliver(actor, order_id)


class Inspection(Command):
    sellable: bool


@router.post("/api/admin/returns/{return_id}/receive")
def receive(return_id: str, command: Inspection, service: Service, actor: User):
    return service.receive_return(actor, return_id, command.sellable)
