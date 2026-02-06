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
        """Get email templates for company"""
        policies = await self.load_policies(db, company_id)
        templates = {}
        for key, value in policies.items():
            if key.startswith("email_template") or key.endswith(".txt"):
                templates[key] = value
        return templates
    
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

