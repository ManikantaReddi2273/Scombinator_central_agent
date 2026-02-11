"""
Summary Agent - Generate executive summary (1-2 lines)
"""
from typing import Dict, Optional
import re


class SummaryAgent:
    """Template-based summary agent for emails"""
    
    def __init__(self):
        # Summary templates based on function + intent
        self.summary_templates = {
            ("Sales", "Inquiry"): "Customer inquiry about {topic} - needs {action}",
            ("Sales", "Follow-up"): "Customer following up on {topic} - {action_needed}",
            ("Sales", "Objection"): "Customer concern about {topic} - requires {action}",
            ("Hiring", "Application"): "Job application received for {role} - {candidate_info}",
            ("Hiring", "Inquiry"): "Hiring inquiry about {role} - {action_needed}",
            ("Support", "Complaint"): "Support issue reported - {issue_type} needs {action}",
            ("Support", "Inquiry"): "Support request about {issue_type} - {action_needed}",
            ("Legal", "Inquiry"): "Legal inquiry regarding {topic} - {action_needed}",
            ("Ops", "Inquiry"): "Operations inquiry about {topic} - {action_needed}",
            ("Marketing", "Inquiry"): "Marketing inquiry about {topic} - {action_needed}",
            ("Admin", "Inquiry"): "General inquiry - {action_needed}"
        }
    
    def generate_summary(
        self,
        subject: str,
        body: str,
        function: str,
        intent: str
    ) -> str:
        """
        Generate executive summary (1-2 lines)
        
        Args:
            subject: Email subject
            body: Email body
            function: Classified function
            intent: Classified intent
            classification: Full classification dict
        
        Returns:
            Executive summary (1-2 lines, no quoting, no fluff)
        """
        # Get template
        template_key = (function, intent)
        template = self.summary_templates.get(template_key)
        
        if not template:
            # Fallback template
            template = "{function} {intent} - {action_needed}"
        
        # Extract variables
        topic = self._extract_topic(subject, body, function)
        action_needed = self._extract_action_needed(intent, function)
        role = self._extract_role(subject, body) if function == "Hiring" else None
        candidate_info = self._extract_candidate_info(body) if function == "Hiring" else None
        issue_type = self._extract_issue_type(subject, body) if function == "Support" else None
        
        # Fill template
        summary = template.format(
            topic=topic or "inquiry",
            action=action_needed,
            action_needed=action_needed,
            role=role or "position",
            candidate_info=candidate_info or "needs review",
            issue_type=issue_type or "issue",
            function=function,
            intent=intent.lower()
        )
        
        # Ensure 1-2 lines maximum
        summary = summary.replace('\n', ' ').strip()
        if len(summary) > 150:
            summary = summary[:147] + "..."
        
        return summary
    
    def _extract_topic(self, subject: str, body: str, function: str) -> Optional[str]:
        """Extract topic from email"""
        text = f"{subject} {body}".lower()
        
        # Common topic keywords
        topic_keywords = {
            "pricing": ["pricing", "price", "cost", "quote"],
            "product": ["product", "feature", "service"],
            "partnership": ["partnership", "partner", "collaboration"],
            "integration": ["integration", "integrate", "api"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                return topic
        
        # Extract from subject (first few words)
        subject_words = subject.split()[:3]
        if subject_words:
            return " ".join(subject_words).lower()
        
        return None
    
    def _extract_action_needed(self, intent: str, function: str) -> str:
        """Extract action needed based on intent and function"""
        action_map = {
            ("Inquiry", "Sales"): "pricing information",
            ("Inquiry", "Hiring"): "job details",
            ("Inquiry", "Support"): "assistance",
            ("Follow-up", "Sales"): "response",
            ("Objection", "Sales"): "addressing concerns",
            ("Application", "Hiring"): "resume review",
            ("Complaint", "Support"): "issue resolution",
            ("Scheduling", "Sales"): "meeting scheduling"
        }
        
        return action_map.get((intent, function), "response")
    
    def _extract_role(self, subject: str, body: str) -> Optional[str]:
        """Extract job role from hiring email"""
        text = f"{subject} {body}".lower()
        
        # Common role keywords
        role_patterns = [
            r"for\s+([a-z\s]+)\s+position",
            r"applying\s+for\s+([a-z\s]+)",
            r"role[:\s]+([a-z\s]+)",
            r"position[:\s]+([a-z\s]+)"
        ]
        
        for pattern in role_patterns:
            match = re.search(pattern, text)
            if match:
                role = match.group(1).strip()
                if len(role) < 50:  # Reasonable role name length
                    return role
        
        return None
    
    def _extract_candidate_info(self, body: str) -> str:
        """Extract candidate information"""
        # Simple extraction - could be enhanced
        if "experience" in body.lower():
            return "experienced candidate"
        elif "fresh" in body.lower() or "new" in body.lower():
            return "new candidate"
        return "candidate"
    
    def _extract_issue_type(self, subject: str, body: str) -> Optional[str]:
        """Extract issue type from support email"""
        text = f"{subject} {body}".lower()
        
        issue_keywords = {
            "login": ["login", "sign in", "authentication"],
            "payment": ["payment", "billing", "invoice", "charge"],
            "feature": ["feature", "functionality", "not working"],
            "bug": ["bug", "error", "broken", "crash"]
        }
        
        for issue_type, keywords in issue_keywords.items():
            if any(keyword in text for keyword in keywords):
                return issue_type
        
        return None


# Singleton instance
summary_agent = SummaryAgent()

