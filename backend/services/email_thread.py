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
