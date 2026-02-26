"""
Flow 2 Orchestrator
Main service that orchestrates the LangGraph workflow for outbound email processing
"""
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import uuid4, UUID
from .state import Flow2State
from .graph import flow2_graph
from models.email import Email
from models.draft import Draft
from models.company import Company
import logging
import json

logger = logging.getLogger(__name__)


class Flow2Orchestrator:
    """Orchestrates Flow 2: Outbound Email → Send using LangGraph"""
    
    def __init__(self):
        self.graph = flow2_graph
    
    async def _initialize_state(
        self,
        company_id: str,
        lead_data: Dict,
        activities: List[Dict],
        intent: Optional[str],
        email_type: str,
        trigger_type: str,
        brand_context: Optional[Dict] = None
    ) -> Flow2State:
        """
        Initialize Flow2State from lead data
        
        Args:
            company_id: Company ID
            lead_data: Full lead record from LEADS.xlsx
            activities: List of previous activities from ACTIVITIES.xlsx
            intent: User-provided intent (if manual trigger)
            email_type: "B2B" or "B2C"
            trigger_type: manual, time_based, calendar, task
            brand_context: Loaded brand context
        
        Returns:
            Initialized Flow2State
        """
        return Flow2State(
            # Step 1: Intent Definition (input)
            company_id=company_id,
            lead_id=lead_data.get("Lead_ID", ""),
            lead_data=lead_data,
            activities=activities,
            email_type=email_type,
            trigger_type=trigger_type,
            user_intent=intent,
            
            # Brand Context
            brand_context=brand_context,
            
            # Step 2-4: Will be populated by nodes
            outbound_intent=None,
            recipient_context=None,
            selected_template_key=None,
            template_content=None,
            required_variables=None,
            draft_subject=None,
            draft_body=None,
            
            # Status
            status="processing",
            error=None
        )
    
    async def _save_to_database(
        self,
        db: AsyncSession,
        state: Flow2State,
        company_email: str
    ) -> Dict[str, str]:
        """
        Save outbound email and draft to database
        
        Args:
            db: Database session
            state: Final Flow2State after graph execution
            company_email: Company's email address (from_email)
            
        Returns:
            Dict with email_id and draft_id
        """
        # Convert company_id to UUID if needed
        company_id_uuid = UUID(state["company_id"]) if isinstance(state["company_id"], str) else state["company_id"]
        
        # Get recipient email from lead data
        recipient_email = state["lead_data"].get("Email", "")
        recipient_context = state.get("recipient_context", {})
        
        # Create email record
        email = Email(
            id=uuid4(),
            company_id=company_id_uuid,
            email_type="outbound",
            subject=state.get("draft_subject", ""),
            body=state.get("draft_body", ""),
            from_email=company_email,
            to_email=recipient_email,
            thread_id=None,  # Outbound emails start new threads
            gmail_message_id=None,  # Will be set when sent
            outbound_intent=state.get("outbound_intent"),
            recipient_context=json.dumps(recipient_context) if recipient_context else None,
            trigger_type=state.get("trigger_type"),
            # Classification fields not used for outbound
            function=None,
            intent=None,
            urgency=None,
            impact=None,
            confidence=None,
            priority_score=None,
            executive_summary=None,
            recommended_action=None,
            classification_metadata=None
        )
        
        try:
            db.add(email)
            await db.flush()  # Flush to get email.id
            
            # Create draft record
            draft = Draft(
                id=uuid4(),
                company_id=company_id_uuid,
                email_id=email.id,
                subject=state.get("draft_subject", ""),
                body=state.get("draft_body", ""),
                status="pending",
                template_used=state.get("selected_template_key"),
                variables_used=json.dumps(state.get("required_variables", {})) if state.get("required_variables") else None
            )
            
            db.add(draft)
            await db.commit()
            
            email_id = str(email.id)
            draft_id = str(draft.id)
            
            logger.info(f"Saved outbound email {email_id} and draft {draft_id} for lead {state['lead_id']}")
            
            return {
                "email_id": email_id,
                "draft_id": draft_id
            }
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Database integrity error saving outbound email: {str(e)}")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving outbound email to database: {str(e)}")
            raise
    
    async def process_outbound(
        self,
        db: AsyncSession,
        company_id: str,
        lead_data: Dict,
        activities: List[Dict],
        intent: Optional[str] = None,
        email_type: str = "B2B",
        trigger_type: str = "manual"
    ) -> Dict:
        """
        Main entry point: Process outbound email through Flow 2 LangGraph workflow
        
        Args:
            db: Database session
            company_id: Company ID
            lead_data: Full lead record from LEADS.xlsx
            activities: List of previous activities from ACTIVITIES.xlsx
            intent: User-provided intent (if manual trigger)
            email_type: "B2B" or "B2C"
            trigger_type: manual, time_based, calendar, task
            
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
            
            # Get company email for from_email field
            result = await db.execute(
                select(Company).where(Company.company_id == UUID(company_id))
            )
            company = result.scalar_one_or_none()
            if not company:
                raise ValueError(f"Company {company_id} not found")
            
            company_email = company.email
            
            # Initialize state
            initial_state = await self._initialize_state(
                company_id=company_id,
                lead_data=lead_data,
                activities=activities,
                intent=intent,
                email_type=email_type,
                trigger_type=trigger_type,
                brand_context=brand_context
            )
            
            # Run LangGraph workflow
            config = {"db": db}
            
            # Execute graph
            final_state = await self.graph.ainvoke(
                initial_state,
                config=config
            )
            
            # Update status
            final_state["status"] = "completed"
            
            # Save to database
            result = await self._save_to_database(db, final_state, company_email)
            
            # Update state with IDs
            final_state["email_id"] = result["email_id"]
            final_state["draft_id"] = result["draft_id"]
            
            # Get recipient info for response
            recipient_context = final_state.get("recipient_context", {})
            recipient_name = recipient_context.get("name", "") if recipient_context else ""
            recipient_company = recipient_context.get("company", "") if recipient_context else ""
            recipient = f"{recipient_name} ({recipient_company})" if recipient_name or recipient_company else ""
            
            return {
                "email_id": result["email_id"],
                "draft_id": result["draft_id"],
                "status": "completed",
                "subject": final_state.get("draft_subject"),
                "body": final_state.get("draft_body"),
                "recipient": recipient
            }
            
        except Exception as e:
            logger.error(f"Flow 2 processing error: {str(e)}", exc_info=True)
            return {
                "email_id": None,
                "draft_id": None,
                "status": "error",
                "error": str(e)
            }

