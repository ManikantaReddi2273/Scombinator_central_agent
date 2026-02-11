"""
Policy loader service for loading company policies from Drive
"""
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.google_api import google_api_service
from services.tenant import tenant_service
import json


class PolicyLoaderService:
    """Service for loading and caching company policies"""
    
    def __init__(self):
        self.google_api = google_api_service
        self.tenant_service = tenant_service
        # In-memory cache (in production, use Redis)
        self._cache: Dict[str, Dict] = {}
    
    async def load_policies(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Dict[str, Optional[str]]:
        """Load all policies for a company"""
        # Check cache first
        cache_key = str(company_id)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get company info
        company = await self.tenant_service.get_company_by_id(db, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        # Load policies from Drive
        policies = await self.google_api.get_policy_files(
            db, company_id, company.name
        )
        
        # Cache policies
        self._cache[cache_key] = policies
        
        return policies
    
    async def get_brand_tone(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Optional[str]:
        """Get brand tone for company"""
        policies = await self.load_policies(db, company_id)
        return policies.get("brand_tone.txt")
    
    async def get_pricing_rules(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Optional[str]:
        """Get pricing rules for company"""
        policies = await self.load_policies(db, company_id)
        return policies.get("pricing_rules.pdf")
    
    async def get_templates(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Dict[str, Optional[str]]:
        """Get email templates for company from Drive"""
        try:
            # Get company info
            company = await self.tenant_service.get_company_by_id(db, company_id)
            if not company:
                return self._get_default_templates()
            
            # Load templates from Drive
            templates = await self.google_api.get_template_files(
                db, company_id, company.name
            )
            
            # If no templates found, use defaults
            if not templates:
                return self._get_default_templates()
            
            return templates
        except Exception as e:
            # Log error but return defaults
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error loading templates for company {company_id}: {str(e)}")
            return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, str]:
        """Get default email templates"""
        return {
            "pricing_inquiry_template.txt": """Thank you for your interest in our pricing.

We'd be happy to provide you with detailed pricing information. Our pricing is customized based on your specific needs.

Would you be available for a brief call this week to discuss your requirements? I can then provide you with a tailored quote.

Best regards""",
            "support_response_template.txt": """Thank you for reaching out to our support team.

We've received your request and our team is looking into it. We'll get back to you as soon as possible.

If this is urgent, please let us know and we'll prioritize your request.

Best regards""",
            "general_response_template.txt": """Thank you for your email.

We've received your message and will respond shortly. If you have any urgent questions, please don't hesitate to reach out.

Best regards""",
            "application_acknowledgment_template.txt": """Thank you for your interest in joining our team.

We've received your application and our hiring team will review it. We'll be in touch if we'd like to move forward.

Best regards"""
        }
    
    async def get_faq(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Optional[Dict]:
        """Get FAQ data for company"""
        policies = await self.load_policies(db, company_id)
        faq_content = policies.get("faq.json")
        if faq_content:
            try:
                return json.loads(faq_content)
            except json.JSONDecodeError:
                return None
        return None
    
    def clear_cache(self, company_id: Optional[str] = None):
        """Clear policy cache"""
        if company_id:
            self._cache.pop(str(company_id), None)
        else:
            self._cache.clear()


# Singleton instance
policy_loader_service = PolicyLoaderService()

