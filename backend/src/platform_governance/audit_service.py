"""Audit logging service (Phase 0 §3.17, Phase 5 §8, Phase 6 §5, INV-33/34).
Every governance action — activation, flag, suspension, RoleAssignment
grant/revoke, Membership transition, including a *denied* self-escalation
attempt — is attributable to a specific actor and is itself an auditable
event, never silently dropped."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.platform_governance.domain.models import AuditActorType, AuditLogEntry
from src.platform_governance.repository import AuditLogRepository


class AuditService:
    def __init__(self, repo: AuditLogRepository) -> None:
        self._repo = repo

    async def record(
        self,
        *,
        org_id: uuid.UUID | None,
        actor_id: uuid.UUID,
        actor_type: AuditActorType,
        action_type: str,
        target_entity: str,
        target_id: uuid.UUID,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            org_id=org_id,
            actor_id=actor_id,
            actor_type=actor_type,
            action_type=action_type,
            target_entity=target_entity,
            target_id=target_id,
            timestamp=datetime.now(timezone.utc),
        )
        return await self._repo.add(entry)
