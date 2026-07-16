"""School evaluation-plan provider (Tier 1 — school operational disclosure)."""
from .adapter import (
    SchoolEvaluationAdapter,
    SchoolPlanResult,
    build_anchor,
    structure_plan,
    MAX_ALL_DOCS,
    MAX_DOWNLOAD_BYTES,
    MIN_USEFUL_MD,
)
from .mcp_client import SchoolMcpClient, REMOTE_SCHOOL_MCP
from . import pii

__all__ = [
    "SchoolEvaluationAdapter",
    "SchoolPlanResult",
    "build_anchor",
    "structure_plan",
    "MAX_ALL_DOCS",
    "MAX_DOWNLOAD_BYTES",
    "MIN_USEFUL_MD",
    "SchoolMcpClient",
    "REMOTE_SCHOOL_MCP",
    "pii",
]
