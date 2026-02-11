"""
Priority Scoring Agent - Calculate priority score (0-100) based on classification
"""
from typing import Dict


class PriorityScorerAgent:
    """Priority scoring agent based on classification signals"""
    
    def __init__(self):
        # Function multipliers
        self.function_multipliers = {
            "Sales": 20,
            "Hiring": 15,
            "Legal": 10,
            "Support": 5,
            "Ops": 3,
            "Marketing": 2,
            "Admin": 0
        }
        
        # Impact multipliers
        self.impact_multipliers = {
            "Revenue": 15,
            "Hiring": 10,
            "Brand": 5,
            "Low": 0
        }
        
        # Urgency multipliers
        self.urgency_multipliers = {
            "Immediate": 10,
            "Soon": 5,
            "Can wait": 0
        }
        
        # Intent multipliers
        self.intent_multipliers = {
            "Inquiry": 5,
            "Follow-up": 3,
            "Objection": 8,  # Needs attention
            "Scheduling": 2,
            "Application": 4,
            "FAQ": 1,
            "Complaint": 7  # Needs attention
        }
        
        # Confidence penalties
        self.confidence_penalties = {
            "Clear": 0,
            "Ambiguous": -5,
            "Missing info": -10
        }
    
    def calculate_score(
        self,
        function: str,
        intent: str,
        urgency: str,
        impact: str,
        confidence: str
    ) -> int:
        """
        Calculate priority score (0-100) based on classification
        
        Args:
            function: Email function (Sales/Hiring/etc)
            intent: Email intent (Inquiry/Follow-up/etc)
            urgency: Email urgency (Immediate/Soon/Can wait)
            impact: Email impact (Revenue/Hiring/Brand/Low)
            confidence: Classification confidence (Clear/Ambiguous/Missing info)
        
        Returns:
            Priority score (0-100)
        """
        # Base score
        score = 50
        
        # Add function multiplier
        score += self.function_multipliers.get(function, 0)
        
        # Add impact multiplier
        score += self.impact_multipliers.get(impact, 0)
        
        # Add urgency multiplier
        score += self.urgency_multipliers.get(urgency, 0)
        
        # Add intent multiplier
        score += self.intent_multipliers.get(intent, 0)
        
        # Apply confidence penalty
        score += self.confidence_penalties.get(confidence, 0)
        
        # Clamp between 0-100
        score = max(0, min(100, score))
        
        return score
    
    def score_from_classification(self, classification: Dict[str, str]) -> int:
        """
        Calculate score from classification dictionary
        
        Args:
            classification: Dict with function, intent, urgency, impact, confidence
        
        Returns:
            Priority score (0-100)
        """
        return self.calculate_score(
            function=classification.get("function", "Admin"),
            intent=classification.get("intent", "Inquiry"),
            urgency=classification.get("urgency", "Can wait"),
            impact=classification.get("impact", "Low"),
            confidence=classification.get("confidence", "Missing info")
        )


# Singleton instance
priority_scorer_agent = PriorityScorerAgent()

