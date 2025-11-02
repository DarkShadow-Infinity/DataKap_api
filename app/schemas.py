"""Pydantic models for the DataKap API."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, constr


class Role(str, Enum):
    ADMIN = "admin"
    LEADER = "leader"
    PROMOTER = "promoter"


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    DELETED = "deleted"


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, List[str]]] = None


class AuthenticatedUser(BaseModel):
    id: str
    email: str
    role: Role
    full_name: Optional[str] = Field(None, alias="fullName")
    phone: Optional[str]

    class Config:
        allow_population_by_field_name = True


class ProfileResponse(AuthenticatedUser):
    api_version: str = Field(alias="apiVersion")

    class Config:
        allow_population_by_field_name = True


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    refresh_token: str = Field(alias="refreshToken")
    expires_in: int = Field(alias="expiresIn")
    user: AuthenticatedUser

    class Config:
        allow_population_by_field_name = True


class CompleteInviteRequest(BaseModel):
    email: str
    temporary_password: str = Field(alias="temporaryPassword")
    verification_code: str = Field(alias="verificationCode")
    new_password: str = Field(alias="newPassword")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")


class RefreshResponse(BaseModel):
    token: str
    expires_in: int = Field(alias="expiresIn")


class RegistrationFields(BaseModel):
    clave_elector: Optional[str] = Field(None, alias="claveElector")
    sexo: Optional[constr(regex="^[MF]$")]
    nombre: Optional[str]
    apellido_paterno: Optional[str] = Field(None, alias="apellidoPaterno")
    apellido_materno: Optional[str] = Field(None, alias="apellidoMaterno")
    direccion: Optional[str]
    codigo_postal: Optional[str] = Field(None, alias="codigoPostal")
    vigencia: Optional[str]
    estado: Optional[str]
    municipio: Optional[str]
    localidad: Optional[str]
    telefono: Optional[str]
    whatsapp: Optional[str]

    class Config:
        allow_population_by_field_name = True


class RegistrationRequest(BaseModel):
    role: Role
    requires_photo: bool = Field(alias="requiresPhoto")
    fields: RegistrationFields


class RegistrationResponse(BaseModel):
    id: str
    status: str


class RegistrationSummaryItem(BaseModel):
    id: str
    role: Role
    requires_photo: bool = Field(alias="requiresPhoto")
    fields: Dict[str, Optional[str]]
    photo_url: Optional[str] = Field(None, alias="photoUrl")
    created_at: datetime = Field(alias="createdAt")
    synced_at: Optional[datetime] = Field(None, alias="syncedAt")
    sync_status: SyncStatus = Field(alias="syncStatus")

    class Config:
        allow_population_by_field_name = True


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class RegistrationListResponse(BaseModel):
    items: List[RegistrationSummaryItem]
    pagination: Pagination


class RegistrationDetailResponse(RegistrationSummaryItem):
    client_request_id: Optional[str] = Field(None, alias="clientRequestId")


class RegistrationUpdateRequest(BaseModel):
    fields: Optional[RegistrationFields] = None
    sync_status: Optional[SyncStatus] = Field(None, alias="syncStatus")

    class Config:
        allow_population_by_field_name = True


class RegistrationSyncItem(BaseModel):
    client_request_id: str = Field(alias="clientRequestId")
    role: Role
    requires_photo: bool = Field(alias="requiresPhoto")
    fields: RegistrationFields
    created_at: datetime = Field(alias="createdAt")

    class Config:
        allow_population_by_field_name = True


class RegistrationSyncRequest(BaseModel):
    payload: List[RegistrationSyncItem]


class RegistrationSyncResult(BaseModel):
    client_request_id: str = Field(alias="clientRequestId")
    status: SyncStatus
    server_id: Optional[str] = Field(None, alias="serverId")

    class Config:
        allow_population_by_field_name = True


class RegistrationSyncResponse(BaseModel):
    results: List[RegistrationSyncResult]


class RegistrationSyncSummary(BaseModel):
    pending: int
    synced_today: int = Field(alias="syncedToday")
    failed: int

    class Config:
        allow_population_by_field_name = True


class AdminUser(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = Field(None, alias="fullName")
    phone: Optional[str]
    role: Role
    goal: Optional[int]
    status: str
    verification_code: Optional[str] = Field(None, alias="verificationCode")
    created_at: datetime = Field(alias="createdAt")

    class Config:
        allow_population_by_field_name = True


class AdminUserListResponse(BaseModel):
    items: List[AdminUser]
    pagination: Pagination


class AdminUserCreateRequest(BaseModel):
    email: str
    full_name: str = Field(alias="fullName")
    phone: str
    role: Role
    goal: Optional[int] = None
    send_email: bool = Field(alias="sendEmail")
    expires_in_hours: int = Field(alias="expiresInHours")

    class Config:
        allow_population_by_field_name = True


class AdminUserCreateResponse(BaseModel):
    id: str
    temporary_password: str = Field(alias="temporaryPassword")
    verification_code: str = Field(alias="verificationCode")
    expires_at: datetime = Field(alias="expiresAt")

    class Config:
        allow_population_by_field_name = True


class AdminUserUpdateRequest(BaseModel):
    goal: Optional[int] = None
    status: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class AdminDashboardSummary(BaseModel):
    promoters: Dict[str, int]
    leaders: Dict[str, int]
    registrations: Dict[str, int]
    api_version: str = Field(alias="apiVersion")

    class Config:
        allow_population_by_field_name = True


class CatalogLocationsResponse(BaseModel):
    states: List[str]
    municipalities: List[str]
    localities: List[str]


class CatalogRolesResponse(BaseModel):
    roles: List[Role]


class LogoutResponse(BaseModel):
    message: str
