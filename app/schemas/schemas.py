from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    role: Literal["worker", "admin"] = "worker"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    geofence_radius_m: int = Field(100, ge=10, le=10000)


class CompanyOut(BaseModel):
    id: int
    name: str
    geofence_radius_m: int
    model_config = ConfigDict(from_attributes=True)


class CompanyUpdate(BaseModel):
    geofence_radius_m: int = Field(..., ge=10, le=10000)


class StoreCreate(BaseModel):
    company_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    address_lines: list[str] = Field(..., min_length=1, max_length=5)
    city: str = Field(..., min_length=1, max_length=120)
    country: str = Field(..., min_length=1, max_length=120)
    state: Optional[str] = Field(None, max_length=120)
    postal_code: Optional[str] = Field(None, max_length=40)


class StoreOut(BaseModel):
    id: int
    company_id: int
    name: str
    geocode_status: str
    custom_radius_m: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    store_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)


class TaskOut(BaseModel):
    id: int
    store_id: int
    title: str
    description: Optional[str] = None
    active: bool
    model_config = ConfigDict(from_attributes=True)


class TaskRunRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    accuracy_m: Optional[float] = Field(default=None, ge=0, le=10000)


class TaskRunOut(BaseModel):
    allowed: bool
    distance_m: float
