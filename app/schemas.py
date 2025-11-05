# file: datakap/schemas.py
"""Pydantic models for the DataKap API (updated for Pydantic v2)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, constr


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
    model_config = ConfigDict(populate_by_name=True)

    id: str
    email: str
    role: Role
    full_name: Optional[str] = Field(None, alias="fullName")
    phone: Optional[str]


class ProfileResponse(AuthenticatedUser):
    model_config = ConfigDict(populate_by_name=True)

    api_version: str = Field(alias="apiVersion")


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str
    refresh_token: str = Field(alias="refreshToken")
    expires_in: int = Field(alias="expiresIn")
    user: AuthenticatedUser


class CompleteInviteRequest(BaseModel):
    email: str
    temporary_password: str = Field(alias="temporaryPassword")
    verification_code: str = Field(alias="verificationCode")
    new_password: str = Field(alias="newPassword")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken")


class RefreshResponse(BaseModel):
    """Response for a successful token refresh."""

    token: str
    expiresIn: int


class RegistrationFields(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    clave_elector: Optional[str] = Field(None, alias="claveElector")
    sexo: Optional[constr(pattern="^[MF]$")]
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


class RegistrationRequest(BaseModel):
    role: Role
    requires_photo: bool = Field(alias="requiresPhoto")
    fields: RegistrationFields


class RegistrationResponse(BaseModel):
    id: str
    status: str


class RegistrationSummaryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    role: Role
    requires_photo: bool = Field(alias="requiresPhoto")
    fields: Dict[str, Optional[str]]
    photo_url: Optional[str] = Field(None, alias="photoUrl")
    created_at: datetime = Field(alias="createdAt")
    synced_at: Optional[datetime] = Field(None, alias="syncedAt")
    sync_status: SyncStatus = Field(alias="syncStatus")


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
    model_config = ConfigDict(populate_by_name=True)

    fields: Optional[RegistrationFields] = None
    sync_status: Optional[SyncStatus] = Field(None, alias="syncStatus")


class RegistrationSyncItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_request_id: str = Field(alias="clientRequestId")
    role: Role
    requires_photo: bool = Field(alias="requiresPhoto")
    fields: RegistrationFields
    created_at: datetime = Field(alias="createdAt")


class RegistrationSyncRequest(BaseModel):
    payload: List[RegistrationSyncItem]


class RegistrationSyncResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_request_id: str = Field(alias="clientRequestId")
    status: SyncStatus
    server_id: Optional[str] = Field(None, alias="serverId")


class RegistrationSyncResponse(BaseModel):
    results: List[RegistrationSyncResult]


class RegistrationSyncSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pending: int
    synced_today: int = Field(alias="syncedToday")
    failed: int


class AdminUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    email: str
    full_name: Optional[str] = Field(None, alias="fullName")
    phone: Optional[str]
    role: Role
    goal: Optional[int]
    status: str
    verification_code: Optional[str] = Field(None, alias="verificationCode")
    created_at: datetime = Field(alias="createdAt")


class AdminUserListResponse(BaseModel):
    items: List[AdminUser]
    pagination: Pagination


class AdminUserCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: str
    full_name: str = Field(alias="fullName")
    phone: str
    role: Role
    goal: Optional[int] = None
    send_email: bool = Field(alias="sendEmail")
    expires_in_hours: int = Field(alias="expiresInHours")


class AdminUserCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    temporary_password: str = Field(alias="temporaryPassword")
    verification_code: str = Field(alias="verificationCode")
    expires_at: datetime = Field(alias="expiresAt")


class AdminUserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    goal: Optional[int] = None
    status: Optional[str] = None


class AdminDashboardSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    promoters: Dict[str, int]
    leaders: Dict[str, int]
    registrations: Dict[str, int]
    api_version: str = Field(alias="apiVersion")


class CatalogLocationsResponse(BaseModel):
    states: List[str]
    municipalities: List[str]
    localities: List[str]


class CatalogRolesResponse(BaseModel):
    roles: List[Role]


class LogoutResponse(BaseModel):
    message: str

class CodigoPostal(BaseModel):
    estado: str
    estado_abreviatura: str
    municipio: str
    centro_reparto: str
    codigo_postal: str
    colonias: List[str]

class CodigoPostalResponse(BaseModel):
    error: bool
    message: str
    codigo_postal: CodigoPostal
