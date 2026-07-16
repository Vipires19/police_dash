"""Campos de auditoria compartilhados (Actor / Target / Origin)."""

from __future__ import annotations

import enum


class AuditOrigin(str, enum.Enum):
    SELF = "SELF"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"
