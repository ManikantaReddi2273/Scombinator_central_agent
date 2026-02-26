"""
Record lead-replied in CRM when an inbound email is a reply in an outbound B2B thread.
Updates ACTIVITIES (Lead Replied), LEADS (Last_Activity_Date, Stage), and TASKS
(mark follow-up tasks Completed, create Review lead reply task).

Only B2B threads: lead_id is resolved from the thread root; the root must be an outbound
email. Normal inbound emails and replies in non-B2B threads do not update CRM (get_lead_id
returns None when root is not outbound).
"""
import logging
from datetime import datetime, timedelta
from uuid import UUID

from time_utils import today_ist_str, now_ist

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.email import Email
from models.company import Company
from services.crm_loader import crm_loader_service
from services.email_thread import get_lead_id_from_thread_root

logger = logging.getLogger(__name__)


async def record_lead_replied_if_applicable(db: AsyncSession, email_id: str) -> None:
    """
    When an inbound email is a reply in an outbound B2B thread, update CRM at receive time:
    - ACTIVITIES: log "Lead Replied" with subject, summary, outcome "Reply received", next action "Review and send reply".
    - LEADS: update Last_Activity_Date and Next_Followup_Date to today, Stage to "Replied".
    - TASKS: mark pending "Check if lead respond" / "Follow-up Email" tasks as Completed; create task "Review lead reply - send response".
    Lead ID is taken from email.recipient_context (set by Flow 1 when saving reply) or resolved from thread root.
    Non-blocking: logs a warning on failure.
    """
    try:
        result = await db.execute(
            select(Email).where(Email.id == UUID(email_id))
        )
        email = result.scalar_one_or_none()
        if not email or not email.thread_id:
            return

        lead_id = None
        rc = email.recipient_context
        if rc:
            if isinstance(rc, dict):
                lead_id = (rc.get("lead_id") or rc.get("Lead_ID") or "").strip()
            elif isinstance(rc, str):
                try:
                    import json
                    data = json.loads(rc)
                    lead_id = (data.get("lead_id") or data.get("Lead_ID") or "").strip()
                except Exception:
                    pass
        if not lead_id:
            lead_id = await get_lead_id_from_thread_root(db, str(email.company_id), email.thread_id)
            lead_id = (lead_id or "").strip() if lead_id else ""
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

        # 1. ACTIVITIES: log "Lead Replied" with clear wording
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

        today_str = today_ist_str("%Y-%m-%d")

        # 2. LEADS: Last_Activity_Date, Next_Followup_Date (today = follow up now), Stage = "Replied"
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

        logger.info("CRM updated for lead replied: lead_id=%s (ACTIVITIES, LEADS, TASKS)", lead_id)
    except Exception as e:
        logger.warning("Could not record lead replied in CRM: %s", e)
