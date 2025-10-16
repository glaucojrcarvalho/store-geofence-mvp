from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


class LoginRequest(BaseModel):
    email: str = Field(...)
    role: Literal["worker", "admin"] = "worker"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CompanyCreate(BaseModel):
    name: str
    geofence_radius_m: int = 100

class CompanyOut(BaseModel):
    id: int
    name: str
    geofence_radius_m: int
    model_config = ConfigDict(from_attributes=True)

class CompanyUpdate(BaseModel):
    geofence_radius_m: int

class StoreCreate(BaseModel):
    company_id: int
    name: str
    address_lines: list[str]
    city: str
    country: str
    state: Optional[str] = None
    postal_code: Optional[str] = None

class StoreOut(BaseModel):
    id: int
    company_id: int
    name: str
    geocode_status: str
    custom_radius_m: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    store_id: int
    title: str
    description: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    store_id: int
    title: str
    description: Optional[str] = None
    active: bool
    model_config = ConfigDict(from_attributes=True)

class TaskRunRequest(BaseModel):
    lat: float
    lng: float
    accuracy_m: Optional[float] = None

class TaskRunOut(BaseModel):
    allowed: bool
    distance_m: float
