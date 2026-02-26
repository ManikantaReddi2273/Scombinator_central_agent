"""
Helpers for email threading: resolve lead_id from thread root (outbound B2B).
Used so replies in an outbound B2B thread can update CRM (LEADS/ACTIVITIES/TASKS).
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.email import Email

logger = logging.getLogger(__name__)


async def get_lead_id_from_thread_root(
    db: AsyncSession,
    company_id: str,
    thread_id: str,
) -> Optional[str]:
    """
    Return lead_id from the thread's root (oldest) email if that email is outbound.
    Used to attach lead context to inbound replies in a B2B thread so CRM can be updated.

    Args:
        db: Database session
        company_id: Company ID (str or UUID)
        thread_id: Gmail thread_id

    Returns:
        lead_id from root email's recipient_context if root is outbound; else None
    """
    if not thread_id or not (company_id or "").strip():
        return None
    try:
        company_uuid = UUID(company_id) if isinstance(company_id, str) else company_id
    except (ValueError, TypeError):
        return None

    try:
        # Oldest email in thread (by created_at) is the root
        result = await db.execute(
            select(Email)
            .where(
                Email.thread_id == thread_id.strip(),
                Email.company_id == company_uuid,
            )
            .order_by(Email.created_at.asc())
            .limit(1)
        )
        root = result.scalar_one_or_none()
        if not root:
            return None
        if (getattr(root, "email_type", None) or "").strip().lower() != "outbound":
            return None
        rc = root.recipient_context
        if not rc:
            return None
        if isinstance(rc, dict):
            return (rc.get("lead_id") or "").strip() or None
        if isinstance(rc, str):
            try:
                data = json.loads(rc)
                return (data.get("lead_id") or "").strip() or None
            except Exception:
                return None
        return None
    except Exception as e:
        logger.warning("get_lead_id_from_thread_root failed: %s", e)
        return None
