"""In-memory storage and helper utilities for the demo API implementation."""
from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from .schemas import (
    AdminDashboardSummary,
    AdminUser,
    AdminUserCreateRequest,
    AdminUserCreateResponse,
    RegistrationDetailResponse,
    RegistrationListResponse,
    RegistrationRequest,
    RegistrationResponse,
    RegistrationSummaryItem,
    RegistrationSyncItem,
    RegistrationSyncResponse,
    RegistrationSyncResult,
    RegistrationSyncSummary,
    Role,
    SyncStatus,
)

API_VERSION = "1.0.0"
TOKEN_TTL_SECONDS = 3600


class InMemoryDatabase:
    """A tiny stateful in-memory database used for the example API."""

    def __init__(self) -> None:
        self._registrations: Dict[str, RegistrationDetailResponse] = {}
        self._users: Dict[str, AdminUser] = {}
        self._user_passwords: Dict[str, str] = {}
        self._tokens: Dict[str, str] = {}
        self._refresh_tokens: Dict[str, str] = {}
        self._client_ids: Dict[str, str] = {}
        self._sync_counter = itertools.count(1)
        self.seed()

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------
    def seed(self) -> None:
        """Populate the database with a couple of demo users and registrations."""
        now = datetime.now(timezone.utc)
        admin = AdminUser(
            id="usr-admin",
            email="admin@datakap.mx",
            full_name="Admin User",
            phone="+52 55 0000 0000",
            role=Role.ADMIN,
            goal=500,
            status="active",
            verification_code="ADM1234",
            created_at=now,
        )
        leader = AdminUser(
            id="usr-leader",
            email="leader@datakap.mx",
            full_name="Leader User",
            phone="+52 55 1111 1111",
            role=Role.LEADER,
            goal=200,
            status="active",
            verification_code="LED1234",
            created_at=now,
        )
        promoter = AdminUser(
            id="usr-promoter",
            email="promoter@datakap.mx",
            full_name="Promoter User",
            phone="+52 55 2222 2222",
            role=Role.PROMOTER,
            goal=150,
            status="active",
            verification_code="PRO1234",
            created_at=now,
        )

        for user, password in (
            (admin, "Admin#2025"),
            (leader, "Leader#2025"),
            (promoter, "Promoter#2025"),
        ):
            self._users[user.id] = user
            self._user_passwords[user.email] = password

        # Initial registrations for sample data
        reg_id = "srv-0001"
        self._registrations[reg_id] = RegistrationDetailResponse(
            id=reg_id,
            role=Role.PROMOTER,
            requires_photo=True,
            fields={"nombre": "Juan", "telefono": "5512345678"},
            photo_url=f"https://cdn.datakap.mx/{reg_id}.jpg",
            created_at=now - timedelta(days=1),
            synced_at=now - timedelta(days=1, minutes=-5),
            sync_status=SyncStatus.SYNCED,
            client_request_id="seed-1",
        )

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------
    def authenticate(self, email: str, password: str) -> Optional[AdminUser]:
        stored = self._user_passwords.get(email)
        if stored and stored == password:
            for user in self._users.values():
                if user.email == email:
                    return user
        return None

    def get_user_by_email(self, email: str) -> Optional[AdminUser]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def issue_tokens(self, user: AdminUser) -> Dict[str, str]:
        token = f"tok-{uuid4()}"
        refresh = f"ref-{uuid4()}"
        self._tokens[token] = user.id
        self._refresh_tokens[refresh] = user.id
        return {"token": token, "refresh_token": refresh}

    def refresh_token(self, refresh_token: str) -> Optional[str]:
        user_id = self._refresh_tokens.get(refresh_token)
        if not user_id:
            return None
        new_token = f"tok-{uuid4()}"
        self._tokens[new_token] = user_id
        return new_token

    def revoke_token(self, token: str) -> None:
        self._tokens.pop(token, None)

    def user_from_token(self, token: str) -> Optional[AdminUser]:
        user_id = self._tokens.get(token)
        if not user_id:
            return None
        return self._users.get(user_id)

    def validate_invite(
        self, email: str, temporary_password: str, verification_code: str
    ) -> Optional[AdminUser]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        stored_password = self._user_passwords.get(email)
        if stored_password != temporary_password:
            return None
        if user.verification_code != verification_code:
            return None
        return user

    def set_password(self, email: str, new_password: str) -> None:
        self._user_passwords[email] = new_password

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    def create_registration(
        self, request: RegistrationRequest, client_request_id: Optional[str]
    ) -> RegistrationResponse:
        existing = self._client_ids.get(client_request_id or "")
        if existing:
            return RegistrationResponse(id=existing, status="duplicate")

        reg_id = f"srv-{next(self._sync_counter):04d}"
        now = datetime.now(timezone.utc)
        detail = RegistrationDetailResponse(
            id=reg_id,
            role=request.role,
            requires_photo=request.requires_photo,
            fields=request.fields.dict(by_alias=True, exclude_none=True),
            photo_url=(f"https://cdn.datakap.mx/{reg_id}.jpg" if request.requires_photo else None),
            created_at=now,
            synced_at=None,
            sync_status=SyncStatus.PENDING,
            client_request_id=client_request_id,
        )
        self._registrations[reg_id] = detail
        if client_request_id:
            self._client_ids[client_request_id] = reg_id
        return RegistrationResponse(id=reg_id, status="pending_validation")

    def list_registrations(
        self,
        page: int,
        limit: int,
        sync_status: Optional[SyncStatus],
        role: Optional[Role],
        from_date: Optional[datetime],
        to_date: Optional[datetime],
    ) -> RegistrationListResponse:
        items = list(self._registrations.values())

        def matches(item: RegistrationDetailResponse) -> bool:
            if sync_status and item.sync_status != sync_status:
                return False
            if role and item.role != role:
                return False
            if from_date and item.created_at < from_date:
                return False
            if to_date and item.created_at > to_date:
                return False
            return True

        filtered = [item for item in items if matches(item)]
        start = (page - 1) * limit
        end = start + limit
        page_items = [
            RegistrationSummaryItem(**item.dict())
            for item in filtered[start:end]
        ]
        pagination = {
            "page": page,
            "limit": limit,
            "total": len(filtered),
        }
        return RegistrationListResponse(items=page_items, pagination=pagination)

    def get_registration(self, reg_id: str) -> Optional[RegistrationDetailResponse]:
        return self._registrations.get(reg_id)

    def update_registration(
        self, reg_id: str, fields: Optional[dict], sync_status: Optional[SyncStatus]
    ) -> Optional[RegistrationDetailResponse]:
        registration = self._registrations.get(reg_id)
        if not registration:
            return None
        data = registration.dict()
        if fields:
            data["fields"].update({k: v for k, v in fields.items() if v is not None})
        if sync_status:
            data["sync_status"] = sync_status
            if sync_status == SyncStatus.SYNCED:
                data["synced_at"] = datetime.now(timezone.utc)
        updated = RegistrationDetailResponse(**data)
        self._registrations[reg_id] = updated
        return updated

    def delete_registration(self, reg_id: str) -> bool:
        registration = self._registrations.get(reg_id)
        if not registration:
            return False
        data = registration.dict()
        data["sync_status"] = SyncStatus.DELETED
        self._registrations[reg_id] = RegistrationDetailResponse(**data)
        return True

    def sync_registrations(
        self, items: List[RegistrationSyncItem]
    ) -> RegistrationSyncResponse:
        results: List[RegistrationSyncResult] = []
        for item in items:
            registration_request = RegistrationRequest(
                role=item.role,
                requiresPhoto=item.requires_photo,
                fields=item.fields,
            )
            response = self.create_registration(
                registration_request, item.client_request_id
            )
            status = SyncStatus.SYNCED if response.status != "duplicate" else SyncStatus.FAILED
            results.append(
                RegistrationSyncResult(
                    client_request_id=item.client_request_id,
                    status=status,
                    server_id=response.id if status == SyncStatus.SYNCED else None,
                )
            )
        return RegistrationSyncResponse(results=results)

    def sync_summary(self) -> RegistrationSyncSummary:
        now = datetime.now(timezone.utc)
        pending = sum(
            1 for r in self._registrations.values() if r.sync_status == SyncStatus.PENDING
        )
        synced_today = sum(
            1
            for r in self._registrations.values()
            if r.sync_status == SyncStatus.SYNCED
            and r.synced_at
            and r.synced_at.date() == now.date()
        )
        failed = sum(
            1 for r in self._registrations.values() if r.sync_status == SyncStatus.FAILED
        )
        return RegistrationSyncSummary(
            pending=pending, synced_today=synced_today, failed=failed
        )

    # ------------------------------------------------------------------
    # Admin helpers
    # ------------------------------------------------------------------
    def list_admin_users(
        self,
        page: int,
        limit: int,
        role: Optional[Role],
        status: Optional[str],
        search: Optional[str],
    ) -> Dict[str, object]:
        users = list(self._users.values())

        def matches(user: AdminUser) -> bool:
            if role and user.role != role:
                return False
            if status and user.status != status:
                return False
            if search:
                haystack = f"{user.full_name or ''} {user.email}".lower()
                if search.lower() not in haystack:
                    return False
            return True

        filtered = [user for user in users if matches(user)]
        start = (page - 1) * limit
        end = start + limit
        page_items = filtered[start:end]
        return {
            "items": page_items,
            "pagination": {"page": page, "limit": limit, "total": len(filtered)},
        }

    def create_admin_user(self, payload: AdminUserCreateRequest) -> AdminUserCreateResponse:
        now = datetime.now(timezone.utc)
        user_id = f"usr-{uuid4().hex[:8]}"
        verification_code = uuid4().hex[:8].upper()
        temporary_password = f"Tmp#{now.year}"
        admin_user = AdminUser(
            id=user_id,
            email=payload.email,
            full_name=payload.full_name,
            phone=payload.phone,
            role=payload.role,
            goal=payload.goal,
            status="pending" if payload.send_email else "active",
            verification_code=verification_code,
            created_at=now,
        )
        self._users[user_id] = admin_user
        self._user_passwords[payload.email] = temporary_password
        expires_at = now + timedelta(hours=payload.expires_in_hours)
        return AdminUserCreateResponse(
            id=user_id,
            temporary_password=temporary_password,
            verification_code=verification_code,
            expires_at=expires_at,
        )

    def get_admin_user(self, user_id: str) -> Optional[AdminUser]:
        return self._users.get(user_id)

    def update_admin_user(
        self, user_id: str, goal: Optional[int], status: Optional[str]
    ) -> Optional[AdminUser]:
        user = self._users.get(user_id)
        if not user:
            return None
        data = user.dict()
        if goal is not None:
            data["goal"] = goal
        if status is not None:
            data["status"] = status
        updated = AdminUser(**data)
        self._users[user_id] = updated
        return updated

    def delete_admin_user(self, user_id: str) -> bool:
        if user_id in self._users:
            self._users[user_id] = AdminUser(
                **{**self._users[user_id].dict(), "status": "disabled"}
            )
            return True
        return False

    def dashboard_summary(self) -> AdminDashboardSummary:
        promoters = {"active": 0, "pending": 0, "rejected": 0}
        leaders = {"active": 0, "pending": 0, "rejected": 0}
        for user in self._users.values():
            if user.role == Role.PROMOTER:
                promoters[user.status] = promoters.get(user.status, 0) + 1
            elif user.role == Role.LEADER:
                leaders[user.status] = leaders.get(user.status, 0) + 1
        registrations = {"today": 0, "thisWeek": 0, "thisMonth": 0}
        now = datetime.now(timezone.utc)
        for registration in self._registrations.values():
            if registration.created_at.date() == now.date():
                registrations["today"] += 1
            if (now - registration.created_at).days < 7:
                registrations["thisWeek"] += 1
            if registration.created_at.month == now.month:
                registrations["thisMonth"] += 1
        return AdminDashboardSummary(
            promoters=promoters,
            leaders=leaders,
            registrations=registrations,
            api_version=API_VERSION,
        )


def get_db() -> InMemoryDatabase:
    """Singleton style accessor used by the FastAPI dependency."""
    global _DB
    try:
        return _DB
    except NameError:
        _DB = InMemoryDatabase()
        return _DB
