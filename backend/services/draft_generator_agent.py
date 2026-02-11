"""
Draft Generation Agent - Generate email drafts from templates
"""
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.policy_loader import policy_loader_service
import re


class DraftGeneratorAgent:
    """Template-based draft generation agent"""
    
    def __init__(self):
        # Template selection mapping
        self.template_mapping = {
            ("Sales", "Inquiry"): "pricing_inquiry_template.txt",
            ("Sales", "Follow-up"): "general_response_template.txt",
            ("Sales", "Objection"): "general_response_template.txt",
            ("Hiring", "Application"): "application_acknowledgment_template.txt",
            ("Hiring", "Inquiry"): "general_response_template.txt",
            ("Support", "Inquiry"): "support_response_template.txt",
            ("Support", "Complaint"): "support_response_template.txt",
            ("Legal", "Inquiry"): "general_response_template.txt",
            ("Ops", "Inquiry"): "general_response_template.txt",
            ("Marketing", "Inquiry"): "general_response_template.txt",
            ("Admin", "Inquiry"): "general_response_template.txt"
        }
    
    async def generate_draft(
        self,
        db: AsyncSession,
        company_id: str,
        email_subject: str,
        email_body: str,
        from_email: str,
        function: str,
        intent: str
    ) -> Dict[str, str]:
        """
        Generate draft email from template
        
        Args:
            db: Database session
            company_id: Company ID
            email_subject: Original email subject
            email_body: Original email body
            from_email: Sender email
            function: Email function
            intent: Email intent
        
        Returns:
            Dict with subject, body, template_used, variables_used
        """
        # Get templates
        templates = await policy_loader_service.get_templates(db, company_id)
        
        # Select template
        template_key = (function, intent)
        template_name = self.template_mapping.get(template_key, "general_response_template.txt")
        
        # Get template content
        template_content = templates.get(template_name)
        if not template_content:
            # Fallback to general template
            template_content = templates.get("general_response_template.txt", "")
            if not template_content:
                template_content = "Thank you for your email. We'll get back to you soon.\n\nBest regards"
        
        # Extract variables from email
        variables = self._extract_variables(email_subject, email_body, from_email)
        
        # Fill template
        draft_body = self._fill_template(template_content, variables)
        
        # Apply brand tone
        brand_tone = await policy_loader_service.get_brand_tone(db, company_id)
        if brand_tone:
            draft_body = self._apply_brand_tone(draft_body, brand_tone)
        
        # Generate subject
        draft_subject = f"Re: {email_subject}"
        
        return {
            "subject": draft_subject,
            "body": draft_body,
            "template_used": template_name,
            "variables_used": variables
        }
    
    def _extract_variables(
        self,
        subject: str,
        body: str,
        from_email: str
    ) -> Dict[str, str]:
        """Extract variables from email for template substitution"""
        # Extract customer name from email
        customer_name = self._extract_customer_name(from_email, body)
        
        # Extract topic from subject/body
        topic = self._extract_topic(subject, body)
        
        return {
            "customer_name": customer_name,
            "topic": topic,
            "from_email": from_email
        }
    
    def _extract_customer_name(self, from_email: str, body: str) -> str:
        """Extract customer name from email"""
        # Try to extract from email address
        name_part = from_email.split("@")[0]
        name_part = name_part.replace(".", " ").replace("_", " ").title()
        
        # Try to extract from body (look for "Hi", "Hello", etc.)
        body_lower = body.lower()
        name_patterns = [
            r"hi\s+([a-z]+)",
            r"hello\s+([a-z]+)",
            r"dear\s+([a-z]+)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, body_lower)
            if match:
                return match.group(1).title()
        
        return name_part or "there"
    
    def _extract_topic(self, subject: str, body: str) -> str:
        """Extract topic from email"""
        # Use subject as topic, or first few words of body
        if subject and len(subject) < 100:
            return subject
        else:
            body_words = body.split()[:10]
            return " ".join(body_words) if body_words else "your inquiry"
    
    def _fill_template(self, template: str, variables: Dict[str, str]) -> str:
        """Fill template with variables"""
        draft = template
        
        # Replace variables
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            if placeholder in draft:
                draft = draft.replace(placeholder, value)
        
        # Remove any remaining placeholders
        draft = re.sub(r"\{[^}]+\}", "", draft)
        
        return draft.strip()
    
    def _apply_brand_tone(self, draft: str, brand_tone: str) -> str:
        """Apply brand tone to draft"""
        tone_lower = brand_tone.lower()
        
        # Formal tone
        if "formal" in tone_lower:
            draft = draft.replace("Hi", "Hello")
            draft = draft.replace("Thanks", "Thank you")
            draft = draft.replace("Best regards", "Sincerely")
        
        # Casual tone
        if "casual" in tone_lower or "friendly" in tone_lower:
            draft = draft.replace("Hello", "Hi")
            draft = draft.replace("Sincerely", "Best regards")
        
        # Short tone
        if "short" in tone_lower or "brief" in tone_lower:
            # Remove extra lines
            lines = [line.strip() for line in draft.split("\n") if line.strip()]
            draft = "\n".join(lines[:5])  # Keep first 5 lines
        
        return draft


# Singleton instance
draft_generator_agent = DraftGeneratorAgent()

