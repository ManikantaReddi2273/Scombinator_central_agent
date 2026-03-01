"""
Helpers for email threading: resolve lead_id and lead_source from thread root (outbound B2B/B2C).
Used so replies in an outbound thread can update CRM (LEADS/B2C_FUNNEL, ACTIVITIES, TASKS).
"""
from __future__ import annotations

import json
import logging
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.email import Email

logger = logging.getLogger(__name__)


def _parse_recipient_context(rc) -> Tuple[Optional[str], Optional[str]]:
    """Parse recipient_context (dict or JSON str) to (lead_id, lead_source)."""
    if not rc:
        return (None, None)
    if isinstance(rc, str):
        try:
            rc = json.loads(rc)
        except Exception:
            return (None, None)
    if not isinstance(rc, dict):
        return (None, None)
    lead_id = (rc.get("lead_id") or rc.get("Lead_ID") or "").strip() or None
    lead_source = (rc.get("lead_source") or "").strip().lower() or None
    return (lead_id, lead_source)


async def get_lead_id_and_source_from_thread_root(
    db: AsyncSession,
    company_id: str,
    thread_id: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (lead_id, lead_source) from the thread's root (oldest) email if that email is outbound.
    lead_source is "b2b" or "b2c" from recipient_context; default "b2b" if missing.

    Returns:
        (lead_id, lead_source) from root email's recipient_context if root is outbound; else (None, None)
    """
    if not thread_id or not (company_id or "").strip():
        return (None, None)
    try:
        company_uuid = UUID(company_id) if isinstance(company_id, str) else company_id
    except (ValueError, TypeError):
        return (None, None)
    try:
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
            return (None, None)
        if (getattr(root, "email_type", None) or "").strip().lower() != "outbound":
            return (None, None)
        lead_id, lead_source = _parse_recipient_context(root.recipient_context)
        if not lead_source:
            lead_source = "b2b"
        return (lead_id, lead_source)
    except Exception as e:
        logger.warning("get_lead_id_and_source_from_thread_root failed: %s", e)
        return (None, None)


async def get_lead_id_from_thread_root(
    db: AsyncSession,
    company_id: str,
    thread_id: str,
) -> Optional[str]:
    """
    Return lead_id from the thread's root (oldest) email if that email is outbound.
    Used to attach lead context to inbound replies so CRM can be updated.

    Returns:
        lead_id from root email's recipient_context if root is outbound; else None
    """
    lead_id, _ = await get_lead_id_and_source_from_thread_root(db, company_id, thread_id)
    return lead_id


async def get_thread_id_for_lead_outbound(
    db: AsyncSession,
    company_id: str,
    lead_id: str,
) -> Optional[str]:
    """
    Return thread_id of the most recent sent outbound email for this lead.
    Used when creating a follow-up draft so the follow-up is in the same Gmail thread.

    Args:
        db: Database session
        company_id: Company ID (str or UUID)
        lead_id: Lead ID from CRM

    Returns:
        thread_id from the most recent outbound email for this lead that has thread_id set; else None
    """
    if not (company_id or "").strip() or not (lead_id or "").strip():
        return None
    try:
        company_uuid = UUID(company_id) if isinstance(company_id, str) else company_id
    except (ValueError, TypeError):
        return None
    lead_id_clean = str(lead_id).strip()
    try:
        result = await db.execute(
            select(Email)
            .where(
                Email.company_id == company_uuid,
                Email.email_type == "outbound",
                Email.thread_id.isnot(None),
            )
            .order_by(Email.created_at.desc())
            .limit(50)
        )
        emails = result.scalars().all()
        for email in emails:
            rc = email.recipient_context
            if not rc:
                continue
            if isinstance(rc, dict):
                lid = (rc.get("lead_id") or rc.get("Lead_ID") or "").strip()
            elif isinstance(rc, str):
                try:
                    data = json.loads(rc)
                    lid = (data.get("lead_id") or data.get("Lead_ID") or "").strip()
                except Exception:
                    continue
            else:
                continue
            if lid == lead_id_clean:
                return (email.thread_id or "").strip() or None
        return None
    except Exception as e:
        logger.warning("get_thread_id_for_lead_outbound failed: %s", e)
        return None
