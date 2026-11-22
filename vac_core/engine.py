"""Small, dependency-free authorization decision engine.

This module decides whether a requester may access a resource for a stated
purpose. It does not fetch data, authenticate users, or replace database RLS.
Callers must supply an authenticated subject identity from a trusted layer.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Grant:
    grant_id: str
    owner_id: str
    subject_id: str
    resource: str
    purpose: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    grant_id: Optional[str] = None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def evaluate(*, grant: Optional[Grant], owner_id: str, subject_id: str,
             resource: str, purpose: str, now: Optional[datetime] = None) -> Decision:
    """Return allow only when one exact, active grant matches every dimension."""
    if grant is None:
        return Decision(False, "no_matching_grant")
    try:
        current = _utc(now or datetime.now(timezone.utc))
        expiry = _utc(grant.expires_at)
        revoked = _utc(grant.revoked_at) if grant.revoked_at else None
    except (TypeError, ValueError):
        return Decision(False, "invalid_timestamp")

    if not all((grant.grant_id, grant.owner_id, grant.subject_id,
                grant.resource, grant.purpose)):
        return Decision(False, "incomplete_grant")
    if grant.owner_id != owner_id:
        return Decision(False, "owner_mismatch")
    if grant.subject_id != subject_id:
        return Decision(False, "subject_mismatch")
    if grant.resource != resource:
        return Decision(False, "resource_mismatch")
    if grant.purpose != purpose:
        return Decision(False, "purpose_mismatch")
    if revoked is not None:
        return Decision(False, "revoked", grant.grant_id)
    if current >= expiry:
        return Decision(False, "expired", grant.grant_id)
    return Decision(True, "authorized", grant.grant_id)
