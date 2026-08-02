from __future__ import annotations

from src.platform_governance.domain.models import AuditLogEntry
from src.shared_kernel.repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLogEntry]):
    model = AuditLogEntry
