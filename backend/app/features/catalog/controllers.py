from typing import Annotated
from fastapi import APIRouter, Depends, Query
from app.dependencies import current_actor, get_catalog
from app.identity import Actor
from app.schemas import Product, ProductPage, ProductInput, Publish, StockAdjustment
from .interfaces import Catalog

router = APIRouter()
Service = Annotated[Catalog, Depends(get_catalog)]
User = Annotated[Actor, Depends(current_actor)]


@router.get("/api/products", response_model=ProductPage)
@router.get("/api/search", response_model=ProductPage)
def products(
    service: Service,
    department: str | None = None,
    category: str | None = None,
    q: str | None = Query(None, max_length=100),
    colour: str | None = None,
    size: str | None = None,
    material: str | None = None,
    available: bool = False,
    sale: bool = False,
    sort: str = "new",
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
):
    return service.list(
        department=department,
        category=category,
        q=q,
        colour=colour,
        size=size,
        material=material,
        available=available,
        sale=sale,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.get("/api/products/{slug}", response_model=Product)
def product(slug: str, service: Service):
    return service.get(slug)


@router.get("/api/admin/products", response_model=ProductPage)
def admin_products(service: Service, actor: User, q: str | None = None):
    return service.list(actor=actor, q=q, limit=100)


@router.get("/api/admin/products/{product_id}", response_model=Product)
def admin_product(product_id: str, service: Service, actor: User):
    return service.get(product_id, actor)


@router.post("/api/admin/products", response_model=Product)
def create(command: ProductInput, actor: User, service: Service):
    return service.save(actor, command)


@router.patch("/api/admin/products/{product_id}", response_model=Product)
def edit(product_id: str, command: ProductInput, actor: User, service: Service):
    return service.save(actor, command, product_id)


@router.post("/api/admin/products/{product_id}/publish", response_model=Product)
def publish(product_id: str, command: Publish, actor: User, service: Service):
    return service.publish(actor, product_id, command.expected_version)


@router.post("/api/admin/products/{product_id}/archive", response_model=Product)
def archive(product_id: str, command: Publish, actor: User, service: Service):
    return service.publish(actor, product_id, command.expected_version, "archived")


@router.post("/api/admin/inventory/adjustments")
def stock(command: StockAdjustment, actor: User, service: Service):
    return service.stock(actor, command)
