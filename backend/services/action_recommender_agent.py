"""
Action Recommendation Agent - Recommend next action based on classification
"""
from typing import Dict


class ActionRecommenderAgent:
    """Rule-based action recommendation agent"""
    
    def __init__(self):
        # Action mapping based on function + intent
        self.action_map = {
            ("Sales", "Inquiry"): "Reply with template",
            ("Sales", "Follow-up"): "Reply with template",
            ("Sales", "Objection"): "Reply with template",
            ("Sales", "Scheduling"): "Schedule meeting",
            ("Hiring", "Application"): "Review resume",
            ("Hiring", "Inquiry"): "Reply with template",
            ("Support", "Inquiry"): "Reply with template",
            ("Support", "Complaint"): "Reply with template",
            ("Legal", "Inquiry"): "Escalate to human",
            ("Ops", "Inquiry"): "Reply with template",
            ("Marketing", "Inquiry"): "Reply with template",
            ("Admin", "Inquiry"): "Reply with template"
        }
    
    def recommend_action(
        self,
        function: str,
        intent: str,
        urgency: str,
        impact: str,
        confidence: str
    ) -> str:
        """
        Recommend action based on classification
        
        Args:
            function: Email function
            intent: Email intent
            urgency: Email urgency
            impact: Email impact
            confidence: Classification confidence
        
        Returns:
            Recommended action
        """
        # Check escalation rules first
        if confidence == "Missing info":
            return "Ask for missing information"
        
        if urgency == "Immediate" and impact == "Revenue":
            return "Escalate to human"
        
        if intent == "Objection" and confidence != "Clear":
            return "Escalate to human"
        
        # Get action from mapping
        action_key = (function, intent)
        action = self.action_map.get(action_key, "Reply with template")
        
        return action
    
    def recommend_from_classification(self, classification: Dict[str, str]) -> str:
        """
        Recommend action from classification dictionary
        
        Args:
            classification: Dict with function, intent, urgency, impact, confidence
        
        Returns:
            Recommended action
        """
        return self.recommend_action(
            function=classification.get("function", "Admin"),
            intent=classification.get("intent", "Inquiry"),
            urgency=classification.get("urgency", "Can wait"),
            impact=classification.get("impact", "Low"),
            confidence=classification.get("confidence", "Missing info")
        )


# Singleton instance
action_recommender_agent = ActionRecommenderAgent()

