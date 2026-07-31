"""Imports every Bounded Context's domain models for their side effect
(registering tables on `Base.metadata`) — the single place Alembic
autogenerate and `Base.metadata.create_all` look to discover the full
schema. No model should be considered "wired up" until it is imported
here.
"""
from src.analysis_decision.domain import models as analysis_decision_models  # noqa: F401
from src.brand_governance.domain import models as brand_governance_models  # noqa: F401
from src.campaign_asset.domain import models as campaign_asset_models  # noqa: F401
from src.identity_access.domain import models as identity_access_models  # noqa: F401
from src.platform_governance.domain import models as platform_governance_models  # noqa: F401
from src.reporting.domain import models as reporting_models  # noqa: F401
from src.shared_kernel.db import Base

__all__ = ["Base"]
