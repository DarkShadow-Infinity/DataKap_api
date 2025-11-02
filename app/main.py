"""FastAPI application implementing the DataKap backend specification."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status

from . import schemas
from .auth import get_admin_user, get_current_user, get_token
from .schemas import (
    AdminDashboardSummary,
    AdminUser,
    AdminUserCreateRequest,
    AdminUserCreateResponse,
    AdminUserListResponse,
    AdminUserUpdateRequest,
    CatalogLocationsResponse,
    CatalogRolesResponse,
    CompleteInviteRequest,
    LoginRequest,
    LoginResponse,
    ProfileResponse,
    RefreshRequest,
    RefreshResponse,
    RegistrationDetailResponse,
    RegistrationListResponse,
    RegistrationRequest,
    RegistrationResponse,
    RegistrationSyncRequest,
    RegistrationSyncResponse,
    RegistrationSyncSummary,
    RegistrationUpdateRequest,
    Role,
    SyncStatus,
)
from .storage import API_VERSION, InMemoryDatabase, TOKEN_TTL_SECONDS, get_db

app = FastAPI(title="DataKap API", version=API_VERSION)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: InMemoryDatabase = Depends(get_db)) -> LoginResponse:
    user = db.authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")
    tokens = db.issue_tokens(user)
    return LoginResponse(
        token=tokens["token"],
        refresh_token=tokens["refresh_token"],
        expires_in=TOKEN_TTL_SECONDS,
        user=schemas.AuthenticatedUser.parse_obj(user.dict(by_alias=True)),
    )


@app.post("/auth/complete-invite", response_model=LoginResponse)
def complete_invite(
    payload: CompleteInviteRequest, db: InMemoryDatabase = Depends(get_db)
) -> LoginResponse:
    user = db.validate_invite(
        payload.email, payload.temporary_password, payload.verification_code
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_VERIFICATION_CODE")
    db.set_password(payload.email, payload.new_password)
    db.update_admin_user(user.id, goal=None, status="active")
    tokens = db.issue_tokens(user)
    return LoginResponse(
        token=tokens["token"],
        refresh_token=tokens["refresh_token"],
        expires_in=TOKEN_TTL_SECONDS,
        user=schemas.AuthenticatedUser.parse_obj(user.dict(by_alias=True)),
    )


@app.post("/auth/refresh", response_model=RefreshResponse)
def refresh_token(
    payload: RefreshRequest, db: InMemoryDatabase = Depends(get_db)
) -> RefreshResponse:
    token = db.refresh_token(payload.refresh_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_REFRESH_TOKEN")
    return RefreshResponse(token=token, expiresIn=TOKEN_TTL_SECONDS)


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: str = Depends(get_token), db: InMemoryDatabase = Depends(get_db)) -> Response:
    db.revoke_token(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@app.get("/profile", response_model=ProfileResponse)
def get_profile(current: schemas.AuthenticatedUser = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse(**current.dict(), api_version=API_VERSION)


# ---------------------------------------------------------------------------
# Registrations
# ---------------------------------------------------------------------------
@app.post("/registrations", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def create_registration(
    payload: RegistrationRequest,
    current: schemas.AuthenticatedUser = Depends(get_current_user),
    db: InMemoryDatabase = Depends(get_db),
    x_client_request_id: Optional[str] = Header(None, alias="X-Client-Request-Id"),
) -> RegistrationResponse:
    return db.create_registration(payload, x_client_request_id)


@app.get("/registrations", response_model=RegistrationListResponse)
def list_registrations(
    page: int = 1,
    limit: int = 20,
    sync_status: Optional[SyncStatus] = Query(None, alias="syncStatus"),
    role: Optional[Role] = None,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    current: schemas.AuthenticatedUser = Depends(get_current_user),
    db: InMemoryDatabase = Depends(get_db),
) -> RegistrationListResponse:
    return db.list_registrations(page, limit, sync_status, role, from_date, to_date)


@app.get("/registrations/{registration_id}", response_model=RegistrationDetailResponse)
def get_registration(
    registration_id: str,
    current: schemas.AuthenticatedUser = Depends(get_current_user),
    db: InMemoryDatabase = Depends(get_db),
) -> RegistrationDetailResponse:
    registration = db.get_registration(registration_id)
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return registration


@app.patch("/registrations/{registration_id}", response_model=RegistrationDetailResponse)
def update_registration(
    registration_id: str,
    payload: RegistrationUpdateRequest,
    current: schemas.AuthenticatedUser = Depends(get_current_user),
    db: InMemoryDatabase = Depends(get_db),
) -> RegistrationDetailResponse:
    registration = db.update_registration(
        registration_id,
        payload.fields.dict(by_alias=True, exclude_none=True) if payload.fields else None,
        payload.sync_status,
    )
    if not registration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return registration


@app.delete("/registrations/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registration(
    registration_id: str,
    current: schemas.AuthenticatedUser = Depends(get_current_user),
    db: InMemoryDatabase = Depends(get_db),
) -> Response:
    if not db.delete_registration(registration_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/registrations/sync", response_model=RegistrationSyncResponse)
def sync_registrations(
    payload: RegistrationSyncRequest,
    current: schemas.AuthenticatedUser = Depends(get_current_user),
    db: InMemoryDatabase = Depends(get_db),
) -> RegistrationSyncResponse:
    return db.sync_registrations(payload.payload)


@app.get("/registrations/sync/summary", response_model=RegistrationSyncSummary)
def sync_summary(
    current: schemas.AuthenticatedUser = Depends(get_current_user),
    db: InMemoryDatabase = Depends(get_db),
) -> RegistrationSyncSummary:
    return db.sync_summary()


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
@app.get("/admin/users", response_model=AdminUserListResponse)
def list_admin_users(
    page: int = 1,
    limit: int = 20,
    role: Optional[Role] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    _: schemas.AuthenticatedUser = Depends(get_admin_user),
    db: InMemoryDatabase = Depends(get_db),
) -> AdminUserListResponse:
    result = db.list_admin_users(page, limit, role, status, search)
    return AdminUserListResponse(
        items=[AdminUser.parse_obj(user.dict(by_alias=True)) for user in result["items"]],
        pagination=result["pagination"],
    )


@app.post("/admin/users", response_model=AdminUserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    payload: AdminUserCreateRequest,
    _: schemas.AuthenticatedUser = Depends(get_admin_user),
    db: InMemoryDatabase = Depends(get_db),
) -> AdminUserCreateResponse:
    return db.create_admin_user(payload)


@app.get("/admin/users/{user_id}", response_model=AdminUser)
def get_admin_user_detail(
    user_id: str,
    _: schemas.AuthenticatedUser = Depends(get_admin_user),
    db: InMemoryDatabase = Depends(get_db),
) -> AdminUser:
    user = db.get_admin_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return AdminUser.parse_obj(user.dict(by_alias=True))


@app.patch("/admin/users/{user_id}", response_model=AdminUser)
def update_admin_user_endpoint(
    user_id: str,
    payload: AdminUserUpdateRequest,
    _: schemas.AuthenticatedUser = Depends(get_admin_user),
    db: InMemoryDatabase = Depends(get_db),
) -> AdminUser:
    user = db.update_admin_user(user_id, payload.goal, payload.status)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return AdminUser.parse_obj(user.dict(by_alias=True))


@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_user_endpoint(
    user_id: str,
    _: schemas.AuthenticatedUser = Depends(get_admin_user),
    db: InMemoryDatabase = Depends(get_db),
) -> Response:
    if not db.delete_admin_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/admin/users/{user_id}/resend-invite", response_model=AdminUserCreateResponse)
def resend_invite(
    user_id: str,
    _: schemas.AuthenticatedUser = Depends(get_admin_user),
    db: InMemoryDatabase = Depends(get_db),
) -> AdminUserCreateResponse:
    user = db.get_admin_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    request = AdminUserCreateRequest(
        email=user.email,
        full_name=user.full_name or "",
        phone=user.phone or "",
        role=user.role,
        goal=user.goal,
        send_email=True,
        expires_in_hours=24,
    )
    return db.create_admin_user(request)


@app.get("/admin/dashboard/summary", response_model=AdminDashboardSummary)
def dashboard_summary(
    _: schemas.AuthenticatedUser = Depends(get_admin_user),
    db: InMemoryDatabase = Depends(get_db),
) -> AdminDashboardSummary:
    return db.dashboard_summary()


# ---------------------------------------------------------------------------
# Catalogs
# ---------------------------------------------------------------------------
LOCATIONS = {
    "states": ["Aguascalientes", "Baja California", "Ciudad de México"],
    "municipalities": {
        "Ciudad de México": ["Álvaro Obregón", "Coyoacán"],
        "Aguascalientes": ["Aguascalientes"],
    },
    "localities": {
        "Álvaro Obregón": ["San Ángel", "Mixcoac"],
        "Coyoacán": ["Del Carmen"],
    },
}


@app.get("/catalogs/locations", response_model=CatalogLocationsResponse)
def catalog_locations(
    state: Optional[str] = None,
    municipality: Optional[str] = None,
    _: schemas.AuthenticatedUser = Depends(get_current_user),
) -> CatalogLocationsResponse:
    states = LOCATIONS["states"]
    municipalities = LOCATIONS["municipalities"].get(state, []) if state else []
    localities = LOCATIONS["localities"].get(municipality, []) if municipality else []
    return CatalogLocationsResponse(
        states=states,
        municipalities=municipalities,
        localities=localities,
    )


@app.get("/catalogs/roles", response_model=CatalogRolesResponse)
def catalog_roles(_: schemas.AuthenticatedUser = Depends(get_current_user)) -> CatalogRolesResponse:
    return CatalogRolesResponse(roles=[Role.ADMIN, Role.LEADER, Role.PROMOTER])


@app.get("/health", tags=["health"])
def healthcheck() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "version": API_VERSION}
