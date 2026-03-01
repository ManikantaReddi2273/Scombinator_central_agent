"""
Record lead-replied in CRM when an inbound email is a reply in an outbound B2B or B2C thread.
Updates ACTIVITIES (Lead Replied), LEADS or B2C_FUNNEL (Stage=Replied, dates), and TASKS.

lead_id and lead_source are resolved from email.recipient_context or from thread root.
B2B: update LEADS; B2C: update B2C_FUNNEL. ACTIVITIES and TASKS use lead_id for both.
"""
import json
import logging
from datetime import timedelta
from uuid import UUID

from time_utils import today_ist_str, now_ist

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.email import Email
from models.company import Company
from services.crm_loader import crm_loader_service
from services.email_thread import get_lead_id_and_source_from_thread_root

logger = logging.getLogger(__name__)


def _parse_rc(rc) -> tuple:
    """Return (lead_id, lead_source) from recipient_context."""
    if not rc:
        return ("", None)
    if isinstance(rc, str):
        try:
            rc = json.loads(rc)
        except Exception:
            return ("", None)
    if not isinstance(rc, dict):
        return ("", None)
    lead_id = (rc.get("lead_id") or rc.get("Lead_ID") or "").strip()
    lead_source = (rc.get("lead_source") or "").strip().lower() or None
    return (lead_id, lead_source)


async def record_lead_replied_if_applicable(db: AsyncSession, email_id: str) -> None:
    """
    When an inbound email is a reply in an outbound B2B or B2C thread, update CRM at receive time:
    - ACTIVITIES: log "Lead Replied".
    - B2B: LEADS (Last_Activity_Date, Next_Followup_Date, Stage=Replied).
    - B2C: B2C_FUNNEL (same fields).
    - TASKS: mark follow-up tasks Completed; create "Review lead reply" task.
    lead_id and lead_source from email.recipient_context or thread root. Non-blocking on failure.
    """
    try:
        result = await db.execute(
            select(Email).where(Email.id == UUID(email_id))
        )
        email = result.scalar_one_or_none()
        if not email or not email.thread_id:
            return

        lead_id, lead_source = _parse_rc(email.recipient_context)
        if not lead_id:
            lead_id, lead_source = await get_lead_id_and_source_from_thread_root(
                db, str(email.company_id), email.thread_id
            )
            lead_id = (lead_id or "").strip()
            lead_source = (lead_source or "b2b").strip().lower()
        if not lead_id:
            return

        company_result = await db.execute(
            select(Company).where(Company.company_id == email.company_id)
        )
        company = company_result.scalar_one_or_none()
        company_name = company.name if company else "System"

        subject = (email.subject or "").strip()
        body_snippet = (email.body or "").strip()[:150]
        summary = f"Lead replied to our email. Subject: {subject or '(no subject)'}. Review and send response."
        if body_snippet:
            summary = f"Lead replied to our email. Subject: {subject or '(no subject)'}. Snippet: {body_snippet}... Review and send response."
        activity_date = email.created_at
        today_str = today_ist_str("%Y-%m-%d")

        # 1. ACTIVITIES: log "Lead Replied" (same for B2B and B2C)
        await crm_loader_service.record_lead_replied(
            db=db,
            company_id=str(email.company_id),
            lead_id=str(lead_id),
            subject=subject or "(no subject)",
            summary_snippet=summary,
            activity_date=activity_date,
            company_name=company_name,
            next_action="Review and send reply",
        )

        is_b2c = lead_source == "b2c"

        if is_b2c:
            # 2a. B2C_FUNNEL: Stage=Replied, Last_Activity_Date, Next_Followup_Date
            try:
                await crm_loader_service.update_b2c_funnel_lead_replied(
                    db=db,
                    company_id=str(email.company_id),
                    b2c_lead_id=str(lead_id),
                    last_activity_date=today_str,
                    next_followup_date=today_str,
                    stage="Replied",
                )
            except Exception as e:
                logger.warning("Could not update B2C_FUNNEL for lead replied (lead_id=%s): %s", lead_id, e)
        else:
            # 2b. LEADS: Last_Activity_Date, Next_Followup_Date, Stage = "Replied"
            try:
                await crm_loader_service.update_lead_activity_dates(
                    db=db,
                    company_id=str(email.company_id),
                    lead_id=str(lead_id),
                    last_activity_date=today_str,
                    next_followup_date=today_str,
                )
                await crm_loader_service.update_lead_stage(
                    db=db,
                    company_id=str(email.company_id),
                    lead_id=str(lead_id),
                    new_stage="Replied",
                )
            except Exception as e:
                logger.warning("Could not update LEADS for lead replied (lead_id=%s): %s", lead_id, e)

        # 3. TASKS: mark "Check if lead respond" / "Follow-up Email" as Completed; create "Review lead reply" task
        try:
            await crm_loader_service.mark_tasks_completed_for_lead_reply(
                db=db,
                company_id=str(email.company_id),
                lead_id=str(lead_id),
            )
        except Exception as e:
            logger.warning("Could not mark tasks completed for lead reply (lead_id=%s): %s", lead_id, e)

        try:
            tomorrow = (now_ist().date() + timedelta(days=1)).strftime("%Y-%m-%d")
            await crm_loader_service.create_followup_task(
                db=db,
                company_id=str(email.company_id),
                lead_id=str(lead_id),
                task_type="Review Reply",
                description="Review lead reply - send response",
                due_date=tomorrow,
                priority="High",
                assigned_to=company_name,
            )
        except Exception as e:
            logger.warning("Could not create Review lead reply task (lead_id=%s): %s", lead_id, e)

        sheet = "B2C_FUNNEL" if is_b2c else "LEADS"
        logger.info("CRM updated for lead replied: lead_id=%s (ACTIVITIES, %s, TASKS)", lead_id, sheet)
    except Exception as e:
        logger.warning("Could not record lead replied in CRM: %s", e)
