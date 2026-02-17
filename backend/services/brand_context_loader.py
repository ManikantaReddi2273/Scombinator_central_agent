"""
Brand Context Loader Service
Loads and caches company brand context documents from Google Drive
"""
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.google_api import google_api_service
from services.tenant import tenant_service
from services.redis_cache import redis_cache
import logging

logger = logging.getLogger(__name__)


class BrandContextLoaderService:
    """Service for loading and caching brand context"""
    
    def __init__(self):
        self.google_api = google_api_service
        self.tenant_service = tenant_service
    
    def _extract_key_points(self, full_context: Dict) -> Dict:
        """
        Extract key points from full context for optimized LLM usage
        
        Args:
            full_context: Full brand context dict
            
        Returns:
            Lightweight dict with key points (~200-300 tokens)
        """
        key_points = {}
        
        # Extract company name from COMPANY.md
        company_content = full_context.get("company", "")
        if company_content:
            # Extract first line or company name
            lines = company_content.split('\n')
            for line in lines:
                if 'Company Name' in line or '**Company Name**' in line or '# ' in line:
                    # Try to extract company name
                    if ':' in line:
                        key_points["company_name"] = line.split(':')[-1].strip().replace('*', '').replace('#', '').strip()
                    elif line.startswith('# '):
                        key_points["company_name"] = line.replace('#', '').strip()
                    else:
                        key_points["company_name"] = line.strip().replace('*', '')
                    break
            if not key_points.get("company_name"):
                # Fallback: use first non-empty line
                for line in lines:
                    if line.strip() and not line.strip().startswith('#'):
                        key_points["company_name"] = line.strip()[:50]  # Limit length
                        break
            if not key_points.get("company_name"):
                key_points["company_name"] = "Company"  # Default
        
        # Extract tone style from VOICE.md
        voice_content = full_context.get("voice", "")
        if voice_content:
            # Look for tone keywords
            tone_keywords = []
            voice_lower = voice_content.lower()
            if "practical" in voice_lower:
                tone_keywords.append("Practical")
            if "friendly" in voice_lower:
                tone_keywords.append("Friendly")
            if "direct" in voice_lower:
                tone_keywords.append("Direct")
            if "professional" in voice_lower:
                tone_keywords.append("Professional")
            if "casual" in voice_lower:
                tone_keywords.append("Casual")
            if "formal" in voice_lower:
                tone_keywords.append("Formal")
            key_points["tone_style"] = ", ".join(tone_keywords) if tone_keywords else "Professional"
        else:
            key_points["tone_style"] = "Professional"
        
        # Extract SLA rules from POLICIES.md
        policies_content = full_context.get("policies", "")
        if policies_content:
            sla_rules = []
            # Look for SLA patterns
            lines = policies_content.split('\n')
            in_sla_section = False
            for line in lines:
                if "Response Time SLAs" in line or "SLA" in line or "response time" in line.lower():
                    in_sla_section = True
                    continue
                if in_sla_section:
                    # Look for rules with time indicators
                    if '|' in line and ('hours' in line.lower() or 'minutes' in line.lower() or 'days' in line.lower()):
                        sla_rules.append(line.strip())
                    elif line.strip().startswith('-') or line.strip().startswith('*'):
                        sla_rules.append(line.strip())
                    elif line.strip() == "" and sla_rules:
                        break
                    if len(sla_rules) >= 5:
                        break
            key_points["sla_rules"] = "\n".join(sla_rules[:5])  # Top 5 rules
        else:
            key_points["sla_rules"] = ""
        
        # Extract pricing policy
        if policies_content:
            policies_lower = policies_content.lower()
            if "no pricing in email" in policies_lower or "pricing" in policies_lower:
                if "no pricing" in policies_lower or "don't discuss pricing" in policies_lower:
                    key_points["pricing_policy"] = "No pricing in email - schedule call"
                else:
                    key_points["pricing_policy"] = "Standard pricing policy"
            else:
                key_points["pricing_policy"] = "Standard pricing policy"
        else:
            key_points["pricing_policy"] = "Standard pricing policy"
        
        # Extract top 5 FAQs from KNOWLEDGE.md
        knowledge_content = full_context.get("knowledge", "")
        if knowledge_content:
            # Extract FAQ questions
            faqs = []
            lines = knowledge_content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('**Q:') or line.strip().startswith('Q:') or line.strip().startswith('### Q:'):
                    question = line.replace('**Q:', '').replace('Q:', '').replace('###', '').strip().replace('*', '')
                    if question and len(question) < 200:
                        faqs.append(question)
                        if len(faqs) >= 5:
                            break
            key_points["top_faqs"] = "\n".join(faqs) if faqs else ""
        else:
            key_points["top_faqs"] = ""
        
        # Template names only (not full content)
        templates = full_context.get("templates", {})
        if isinstance(templates, dict):
            key_points["template_names"] = list(templates.keys())[:10]  # Top 10 template names
        else:
            key_points["template_names"] = []
        
        return key_points
    
    async def load_all(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Dict:
        """
        Load all brand context for a company (with caching)
        
        Args:
            db: Database session
            company_id: Company ID
            
        Returns:
            Dict with structure: {"full": {...}, "key_points": {...}}
        """
        # Check cache first
        cache_key = f"brand_context:{company_id}"
        cached = await redis_cache.get(cache_key)
        
        if cached:
            logger.info(f"Brand context loaded from cache for company {company_id}")
            return cached
        
        # Not in cache - load from Drive
        logger.info(f"Loading brand context from Drive for company {company_id}")
        
        # Get company info
        company = await self.tenant_service.get_company_by_id(db, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        # Load from Drive
        full_context = await self.google_api.load_brand_context_folder(
            db, company_id, company.name
        )
        
        # Extract key points for optimization
        key_points = self._extract_key_points(full_context)
        
        # Structure brand context
        brand_context = {
            "full": full_context,  # Full documents for draft generation
            "key_points": key_points  # Extracted points for other nodes
        }
        
        # Cache for 1 hour
        await redis_cache.set(cache_key, brand_context, ttl=3600)
        
        logger.info(f"Brand context loaded and cached for company {company_id}")
        return brand_context
    
    async def get_company_info(self, db: AsyncSession, company_id: str) -> Optional[str]:
        """Get company info (COMPANY.md)"""
        context = await self.load_all(db, company_id)
        return context.get("full", {}).get("company")
    
    async def get_voice(self, db: AsyncSession, company_id: str) -> Optional[str]:
        """Get brand voice (VOICE.md)"""
        context = await self.load_all(db, company_id)
        return context.get("full", {}).get("voice")
    
    async def get_playbooks(self, db: AsyncSession, company_id: str) -> Optional[str]:
        """Get playbooks (PLAYBOOKS.md)"""
        context = await self.load_all(db, company_id)
        return context.get("full", {}).get("playbooks")
    
    async def get_policies(self, db: AsyncSession, company_id: str) -> Optional[str]:
        """Get policies (POLICIES.md)"""
        context = await self.load_all(db, company_id)
        return context.get("full", {}).get("policies")
    
    async def get_knowledge(self, db: AsyncSession, company_id: str) -> Optional[str]:
        """Get knowledge base (KNOWLEDGE.md)"""
        context = await self.load_all(db, company_id)
        return context.get("full", {}).get("knowledge")
    
    async def get_templates(self, db: AsyncSession, company_id: str) -> Dict:
        """Get all templates"""
        context = await self.load_all(db, company_id)
        return context.get("full", {}).get("templates", {})
    
    async def refresh_cache(self, db: AsyncSession, company_id: str):
        """
        Manually refresh brand context cache
        
        Args:
            db: Database session
            company_id: Company ID
            
        Returns:
            Refreshed brand context dict
        """
        cache_key = f"brand_context:{company_id}"
        await redis_cache.delete(cache_key)
        # Reload will happen on next access
        logger.info(f"Cache refreshed for company {company_id}")
        return await self.load_all(db, company_id)


# Singleton instance
brand_context_loader = BrandContextLoaderService()

