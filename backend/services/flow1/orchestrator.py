"""
Flow 1 Orchestrator
Main service that orchestrates the LangGraph workflow for email processing
"""
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import uuid4, UUID
from .state import Flow1State
from .graph import flow1_graph
from models.email import Email
from models.draft import Draft
from services.email_thread import get_lead_id_from_thread_root
import logging

logger = logging.getLogger(__name__)


class Flow1Orchestrator:
    """Orchestrates Flow 1: Inbound Email → Response using LangGraph"""
    
    def __init__(self):
        self.graph = flow1_graph
    
    async def _load_thread_history(
        self,
        db: AsyncSession,
        company_id: str,
        thread_id: Optional[str],
        current_gmail_message_id: Optional[str] = None
    ) -> list:
        """
        Load previous emails from the same thread for context
        
        Args:
            db: Database session
            company_id: Company ID
            thread_id: Thread ID to query
            current_gmail_message_id: Current email's gmail_message_id to exclude
            
        Returns:
            List of dicts with previous email data (subject, body, from_email, created_at)
        """
        if not thread_id:
            return []
        
        try:
            # First, get all emails in thread (excluding current)
            base_query = select(Email).where(
                Email.thread_id == thread_id,
                Email.company_id == UUID(company_id)
            )
            
            # Exclude current email if gmail_message_id is provided
            if current_gmail_message_id:
                base_query = base_query.where(Email.gmail_message_id != current_gmail_message_id)
            
            # Get the most recent 5 emails (order by created_at DESC, then limit, then reverse for chronological order)
            # This ensures we get the most recent context while maintaining chronological order in the list
            query = base_query.order_by(Email.created_at.desc()).limit(5)
            
            result = await db.execute(query)
            previous_emails = result.scalars().all()
            
            # Reverse to get chronological order (oldest first) for better context flow
            previous_emails = list(reversed(previous_emails))
            
            # Format for context
            history = []
            for email in previous_emails:
                # Include more body text for better context (increased from 500 to 1000 chars)
                body_text = email.body[:1000] if len(email.body) > 1000 else email.body
                history.append({
                    "subject": email.subject,
                    "body": body_text,
                    "from_email": email.from_email,
                    "created_at": email.created_at.isoformat() if email.created_at else None,
                    "was_reply": email.subject.startswith("Re:") or email.subject.startswith("RE:"),
                    "email_type": (email.email_type or "inbound").strip().lower(),
                })
            
            logger.info(f"Loaded {len(history)} previous emails from thread {thread_id}")
            return history
            
        except Exception as e:
            logger.warning(f"Error loading thread history for thread_id={thread_id}: {str(e)}")
            return []
    
    async def _initialize_state(
        self,
        company_id: str,
        email_data: Dict,
        db: Optional[AsyncSession] = None,
        brand_context: Optional[Dict] = None
    ) -> Flow1State:
        """
        Initialize Flow1State from email data and load thread history if available
        
        Args:
            company_id: Company ID
            email_data: Email data dict with subject, body, from, to, etc.
            db: Database session (optional, needed for thread history)
            
        Returns:
            Initialized Flow1State with thread history if available
        """
        thread_id = email_data.get("thread_id")
        gmail_message_id = email_data.get("gmail_message_id")
        
        # Load thread history if thread_id exists and db is available
        thread_history = []
        thread_count = 0
        if thread_id and db:
            thread_history = await self._load_thread_history(
                db=db,
                company_id=company_id,
                thread_id=thread_id,
                current_gmail_message_id=gmail_message_id
            )
            thread_count = len(thread_history)
        
        return Flow1State(
            # Step 1: Email Ingestion (input)
            company_id=company_id,
            email_subject=email_data.get("subject", ""),
            email_body=email_data.get("body", ""),
            from_email=email_data.get("from", ""),
            to_email=email_data.get("to", ""),
            thread_id=thread_id,
            gmail_message_id=gmail_message_id,
            thread_history=thread_history,  # Always a list (empty if no history)
            thread_count=thread_count,  # Always an int (0 if new thread)
            
            # Step 2-6: Will be populated by nodes
            function=None,
            intent=None,
            urgency=None,
            impact=None,
            confidence=None,
            classification_metadata=None,
            priority_score=None,
            executive_summary=None,
            recommended_action=None,
            draft_subject=None,
            draft_body=None,
            template_used=None,
            variables_used=None,
            
            # Step 7: Metadata
            email_id=None,
            draft_id=None,
            status="processing",
            error_message=None,
            
            # Brand Context
            brand_context=brand_context
        )
    
    async def _save_to_database(
        self,
        db: AsyncSession,
        state: Flow1State
    ) -> Dict[str, str]:
        """
        Save processed email and draft to database
        
        Args:
            db: Database session
            state: Final Flow1State after graph execution
            
        Returns:
            Dict with email_id and draft_id
        """
        # Convert company_id to UUID if needed
        company_id_uuid = UUID(state["company_id"]) if isinstance(state["company_id"], str) else state["company_id"]
        
        # CRITICAL: Check for duplicate gmail_message_id BEFORE inserting
        # This prevents most duplicate inserts, but race conditions can still occur
        gmail_message_id = state.get("gmail_message_id")
        if gmail_message_id:
            try:
                # Use selectinload to eagerly load drafts if they exist
                from sqlalchemy.orm import selectinload
                existing_result = await db.execute(
                    select(Email)
                    .options(selectinload(Email.drafts))
                    .where(Email.gmail_message_id == gmail_message_id)
                )
                existing = existing_result.scalar_one_or_none()
                if existing:
                    logger.info(f"Duplicate email detected (pre-check): gmail_message_id={gmail_message_id}, returning existing email_id={existing.id}")
                    # Return existing email record
                    email_id = str(existing.id)
                    # Check if draft exists for this email
                    draft_id = None
                    if existing.drafts and len(existing.drafts) > 0:
                        draft_id = str(existing.drafts[0].id)
                    return {
                        "email_id": email_id,
                        "draft_id": draft_id,
                        "status": "duplicate_skipped"
                    }
            except Exception as e:
                logger.warning(f"Error checking for duplicate email: {str(e)}, proceeding with insert")
        
        # Create email record
        email_record = Email(
            id=uuid4(),
            company_id=company_id_uuid,
            subject=state["email_subject"],
            body=state["email_body"],
            from_email=state["from_email"],
            to_email=state["to_email"],
            thread_id=state.get("thread_id"),
            gmail_message_id=gmail_message_id,
            # Classification fields
            function=state.get("function", "Admin"),
            intent=state.get("intent", "Inquiry"),
            urgency=state.get("urgency", "Can wait"),
            impact=state.get("impact", "Low"),
            confidence=state.get("confidence", "Missing info"),
            priority_score=str(state.get("priority_score", 50)),
            executive_summary=state.get("executive_summary"),
            recommended_action=state.get("recommended_action"),
            classification_metadata=state.get("classification_metadata") or {}
        )
        # If this is a reply in a thread, attach lead_id from thread root (outbound B2B) so CRM can be updated when we send the reply
        thread_id = state.get("thread_id")
        if thread_id:
            lead_id = await get_lead_id_from_thread_root(db, state["company_id"], thread_id)
            if lead_id:
                email_record.recipient_context = {"lead_id": lead_id}
                logger.info("Inbound reply in B2B thread: attached lead_id=%s from thread root", lead_id)

        try:
            db.add(email_record)
            await db.commit()
            await db.refresh(email_record)
            email_id = str(email_record.id)
        except IntegrityError as e:
            # Handle race condition: another process inserted the same email
            await db.rollback()
            logger.warning(f"IntegrityError during email insert (likely duplicate): {str(e)}")
            
            # Try to find the existing email after rollback
            # After rollback, the session should still be usable for queries
            if gmail_message_id:
                try:
                    # Query for existing email - this should work after rollback
                    existing_result = await db.execute(
                        select(Email).where(Email.gmail_message_id == gmail_message_id)
                    )
                    existing = existing_result.scalar_one_or_none()
                    if existing:
                        logger.info(f"Found existing email after IntegrityError: email_id={existing.id}")
                        email_id = str(existing.id)
                        draft_id = None
                        # Try to access drafts - they might be lazy loaded
                        try:
                            # Use selectinload to ensure drafts are loaded
                            from sqlalchemy.orm import selectinload
                            existing_result_with_drafts = await db.execute(
                                select(Email)
                                .options(selectinload(Email.drafts))
                                .where(Email.gmail_message_id == gmail_message_id)
                            )
                            existing_with_drafts = existing_result_with_drafts.scalar_one_or_none()
                            if existing_with_drafts and existing_with_drafts.drafts:
                                draft_id = str(existing_with_drafts.drafts[0].id)
                        except Exception as draft_error:
                            logger.debug(f"Could not load drafts for existing email: {str(draft_error)}")
                            # That's OK, draft_id will remain None
                        
                        return {
                            "email_id": email_id,
                            "draft_id": draft_id
                        }
                except Exception as lookup_error:
                    logger.error(f"Error looking up existing email after IntegrityError: {str(lookup_error)}")
            
            # If we can't find existing, return success anyway to prevent workflow failure
            # The email was already processed by another request, so this is not really an error
            logger.info(f"Duplicate email detected (gmail_message_id={gmail_message_id}) - email was already processed. Returning success to prevent workflow failure.")
            return {
                "email_id": None,  # We don't know the ID, but that's OK
                "draft_id": None,
                "status": "duplicate_skipped",
                "message": f"Email with gmail_message_id={gmail_message_id} was already processed"
            }
        
        # Create draft if generated (for any action that produces a draft)
        draft_id = None
        draft_action = state.get("recommended_action")
        # Generate draft for: "Reply with template", "Ask for missing information", "Schedule meeting"
        if state.get("draft_body") and draft_action in ["Reply with template", "Ask for missing information", "Schedule meeting"]:
            try:
                draft = Draft(
                    id=uuid4(),
                    company_id=email_record.company_id,
                    email_id=email_record.id,
                    subject=state.get("draft_subject", f"Re: {state['email_subject']}"),
                    body=state.get("draft_body", ""),
                    status="pending",
                    version="1.0",
                    template_used=state.get("template_used", "openai_generated"),
                    variables_used=str(state.get("variables_used") or {})
                )
                
                db.add(draft)
                await db.commit()
                await db.refresh(draft)
                draft_id = str(draft.id)
            except Exception as e:
                logger.error(f"Error creating draft for email {email_id}: {str(e)}")
                # Don't fail email processing if draft creation fails
        
        return {
            "email_id": email_id,
            "draft_id": draft_id
        }
    
    async def process_email(
        self,
        db: AsyncSession,
        company_id: str,
        email_data: Dict
    ) -> Dict:
        """
        Main entry point: Process email through Flow 1 LangGraph workflow
        
        Args:
            db: Database session
            company_id: Company ID
            email_data: Email data dict with subject, body, from, to, thread_id, gmail_message_id
            
        Returns:
            Dict with email_id, draft_id, and status
        """
        try:
            # Load brand context ONCE before graph execution
            brand_context = None
            try:
                from services.brand_context_loader import brand_context_loader
                brand_context = await brand_context_loader.load_all(db, company_id)
                logger.info(f"Brand context loaded for company {company_id}")
            except Exception as e:
                logger.warning(f"Error loading brand context for company {company_id}: {str(e)}. Continuing without it.")
                # Continue without brand context - nodes will handle None gracefully
            
            # Initialize state (await the async method)
            initial_state = await self._initialize_state(company_id, email_data, db=db, brand_context=brand_context)
            
            # Run LangGraph workflow with config (pass db for draft generator)
            config = {"db": db}
            
            # Execute graph
            final_state = await self.graph.ainvoke(
                initial_state,
                config=config
            )
            
            # Update status
            final_state["status"] = "completed"
            
            # Save to database
            result = await self._save_to_database(db, final_state)
            
            # Update state with IDs
            final_state["email_id"] = result["email_id"]
            final_state["draft_id"] = result["draft_id"]
            
            return {
                "email_id": result["email_id"],
                "draft_id": result["draft_id"],
                "status": "completed",
                "classification": {
                    "function": final_state.get("function"),
                    "intent": final_state.get("intent"),
                    "urgency": final_state.get("urgency"),
                    "impact": final_state.get("impact"),
                    "confidence": final_state.get("confidence"),
                    "priority_score": final_state.get("priority_score"),
                },
                "executive_summary": final_state.get("executive_summary"),
                "recommended_action": final_state.get("recommended_action"),
            }
            
        except Exception as e:
            logger.error(f"Error processing email through Flow 1: {str(e)}", exc_info=True)
            
            # Try to save partial results if possible
            try:
                # Don't await here - we're in error handling, just create a simple dict
                error_state = {
                    "company_id": company_id,
                    "email_subject": email_data.get("subject", ""),
                    "email_body": email_data.get("body", ""),
                    "from_email": email_data.get("from", ""),
                    "to_email": email_data.get("to", ""),
                    "thread_id": email_data.get("thread_id"),
                    "gmail_message_id": email_data.get("gmail_message_id"),
                    "thread_history": [],
                    "thread_count": 0,
                    "status": "error",
                    "error_message": str(e)
                }
                
                # Convert company_id to UUID if needed
                company_id_uuid = UUID(company_id) if isinstance(company_id, str) else company_id
                
                # Save email record with error status
                email_record = Email(
                    id=uuid4(),
                    company_id=company_id_uuid,
                    subject=email_data.get("subject", ""),
                    body=email_data.get("body", ""),
                    from_email=email_data.get("from", ""),
                    to_email=email_data.get("to", ""),
                    thread_id=email_data.get("thread_id"),
                    gmail_message_id=email_data.get("gmail_message_id"),
                    function="Admin",
                    intent="Inquiry",
                    urgency="Can wait",
                    impact="Low",
                    confidence="Missing info",
                    priority_score="50",
                    executive_summary=f"Error processing email: {str(e)}",
                    recommended_action="Escalate to human",
                    classification_metadata={"error": str(e)}
                )
                
                db.add(email_record)
                await db.commit()
                await db.refresh(email_record)
                
                return {
                    "email_id": str(email_record.id),
                    "draft_id": None,
                    "status": "error",
                    "error": str(e)
                }
            except Exception as save_error:
                logger.error(f"Error saving error state: {str(save_error)}")
                raise e


# Singleton instance
flow1_orchestrator = Flow1Orchestrator()

