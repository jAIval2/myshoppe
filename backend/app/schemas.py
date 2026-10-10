from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from app.adapters.storage import approved_media_src


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Media(Command):
    src: str = Field(min_length=1, max_length=2000)
    alt: str = Field(min_length=3, max_length=250)
    role: Literal["lead", "continuation", "cutout", "editorial"] = "lead"

    @field_validator("src")
    @classmethod
    def approved_media(cls, value):
        if not approved_media_src(value):
            raise ValueError("Use an uploaded image or an approved MyShoppe media asset")
        return value


class VariantInput(Command):
    id: str | None = None
    sku: str = Field(min_length=2, max_length=80)
    colour: str = Field(min_length=1, max_length=60)
    colour_hex: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    size: str = Field(min_length=1, max_length=80)
    dimensions: str | None = None
    price_paise: int = Field(strict=True, gt=0, le=100_000_000)
    compare_at_paise: int | None = Field(default=None, strict=True, gt=0)

    @model_validator(mode="after")
    def sale(self):
        if self.compare_at_paise is not None and self.compare_at_paise <= self.price_paise:
            raise ValueError("Compare-at price must exceed selling price")
        return self


class Variant(VariantInput):
    model_config = ConfigDict(extra="ignore")
    id: str
    active: bool = True
    available: int
    on_hand: int = 0
    reserved: int = 0


class ProductInput(Command):
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=150)
    department: Literal["women", "home"]
    category: str = Field(min_length=2, max_length=60)
    description: str = Field(min_length=10, max_length=5000)
    material: str = Field(min_length=2, max_length=200)
    care: str = Field(min_length=2, max_length=1000)
    details: dict[str, str] = Field(default_factory=dict)
    media: list[Media] = Field(min_length=1, max_length=20)
    variants: list[VariantInput] = Field(min_length=1, max_length=100)
    expected_version: int | None = None
    relations: dict[str, list[str]] = Field(default_factory=dict)


class Product(ProductInput):
    model_config = ConfigDict(extra="ignore")
    id: str
    status: str
    version: int
    variants: list[Variant]
    price_paise: int


class ProductPage(BaseModel):
    items: list[Product]
    total: int
    page: int
    pages: int


class Publish(Command):
    expected_version: int


class StockAdjustment(Command):
    variant_id: str
    delta: int = Field(strict=True, ge=-100000, le=100000)
    reason: str = Field(min_length=3, max_length=300)
    request_key: str = Field(min_length=8, max_length=100)


class CartMutation(Command):
    variant_id: str
    quantity: int = Field(strict=True, ge=0, le=10)
    expected_version: int


class Address(Command):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=254)
    phone: str = Field(pattern=r"^[6-9][0-9]{9}$")
    line1: str = Field(min_length=5, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pin: str = Field(pattern=r"^[1-9][0-9]{5}$")


class Checkout(Command):
    address: Address
    quote_hash: str
    request_key: str = Field(min_length=8, max_length=100)


class RefundInput(Command):
    amount: int = Field(strict=True, gt=0)
    reason: str = Field(min_length=3, max_length=300)
    request_key: str = Field(min_length=8, max_length=100)


class ShipmentInput(Command):
    tracking: str = Field(min_length=3, max_length=300)
    items: dict[str, int]

    @model_validator(mode="after")
    def quantities(self):
        if not self.items or any(type(q) is not int or q < 1 for q in self.items.values()):
            raise ValueError("Select positive quantities")
        return self


class ReturnInput(ShipmentInput):
    tracking: str = "return"
    reason: str = Field(min_length=3, max_length=500)
    request_key: str = Field(min_length=8, max_length=100)


class CampaignBlock(Command):
    type: Literal["hero", "video", "poster", "collection-entry"]
    src: str = ""
    mobile_src: str = ""
    poster: str = ""
    title: str = Field(default="", max_length=240)
    subtitle: str = Field(default="", max_length=240)
    tone: Literal["light", "dark"] = "dark"
    layout: Literal["full", "split", "inset"] = "full"
    target: str = Field(pattern=r"^/collections/(women|home)-[a-z-]+$")

    @field_validator("src", "mobile_src", "poster")
    @classmethod
    def approved_media(cls, value):
        if value and not approved_media_src(value):
            raise ValueError("Use an uploaded campaign media asset")
        return value


class CampaignInput(Command):
    expected_revision: int
    blocks: list[CampaignBlock] = Field(min_length=5, max_length=10)

    @model_validator(mode="after")
    def sequence(self):
        types = [b.type for b in self.blocks]
        if (
            types[:2] != ["hero", "video"]
            or types[-1] != "collection-entry"
            or any(t != "poster" for t in types[2:-1])
        ):
            raise ValueError("Required order: hero, video, at least two posters, collection-entry")
        for b in self.blocks[:-1]:
            if not approved_media_src(b.src):
                raise ValueError("Use a processed local media asset")
        return self


class SupportInput(Command):
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=5000)
    request_key: str = Field(min_length=8, max_length=100)
