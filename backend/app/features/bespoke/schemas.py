from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Pin(BaseModel):
    part: str = Field(max_length=80)
    note: str = Field(min_length=1, max_length=1000)
    x: float = Field(default=50, ge=0, le=100)
    y: float = Field(default=50, ge=0, le=100)


class Reference(BaseModel):
    asset_id: str = Field(max_length=36)
    name: str = Field(max_length=120)
    pins: list[Pin] = Field(default_factory=list, max_length=20)


class Design(BaseModel):
    model_config = ConfigDict(str_max_length=2000, extra="forbid")
    name: str = ""
    occasion: str = ""
    requested_date: date | None = None
    fabric: str = ""
    laces: list[str] = Field(default_factory=list, max_length=6)
    lace_choice: Literal["", "selected", "none", "help"] = ""
    quantity: str = ""
    placement: str = ""
    vision: str = ""
    silhouette: str = ""
    neckline: str = ""
    sleeves: str = ""
    length: str = ""
    bottom: str = ""
    dupatta: str = ""
    fit: str = ""
    units: Literal["cm", "in"] = "cm"
    measurements: str = ""
    fitting_plan: str = ""
    references: list[Reference] = Field(default_factory=list, max_length=6)
    voice_id: str = Field(default="", max_length=36)


class Save(BaseModel):
    expected_version: int = Field(ge=1)
    design: Design


class Action(BaseModel):
    expected_version: int = Field(ge=1)
    action: Literal["submit", "agree", "review", "ready"]
    instructions: str = Field(default="", max_length=6000)
    questions: str = Field(default="", max_length=3000)
    material_confirmation: str = Field(default="", max_length=2000)
    measurement_confirmation: str = Field(default="", max_length=2000)
