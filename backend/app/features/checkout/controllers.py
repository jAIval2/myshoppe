from typing import Annotated
from fastapi import APIRouter, Depends
from app.dependencies import current_actor, get_checkout
from app.identity import Actor
from app.schemas import CartMutation, Address, Checkout, Product
from .interfaces import CheckoutCommands

router = APIRouter()
Service = Annotated[CheckoutCommands, Depends(get_checkout)]
User = Annotated[Actor, Depends(current_actor)]


@router.get("/api/cart")
def cart(service: Service, actor: User):
    return service.cart(actor)


@router.put("/api/cart/items")
def mutate(command: CartMutation, service: Service, actor: User):
    return service.mutate(actor, command)


@router.get("/api/favourites", response_model=list[Product])
def favourites(service: Service, actor: User):
    return service.saved(actor)


@router.put("/api/favourites/{product_id}")
def save(product_id: str, service: Service, actor: User):
    return service.save(actor, product_id)


@router.delete("/api/favourites/{product_id}")
def unsave(product_id: str, service: Service, actor: User):
    return service.save(actor, product_id, True)


@router.post("/api/checkout/quote")
def quote(address: Address, service: Service, actor: User):
    return service.quote(actor, address)


@router.post("/api/checkout/attempts")
def attempt(command: Checkout, service: Service, actor: User):
    return service.reserve(actor, command)
