"""
Classification Agent - Rule-based email classification
"""
from typing import Dict, Optional
import re


class ClassificationAgent:
    """Rule-based classification agent for emails"""
    
    def __init__(self):
        # Function keywords
        self.function_keywords = {
            "Sales": ["pricing", "price", "cost", "quote", "purchase", "buy", "sales", "product", "service"],
            "Hiring": ["resume", "cv", "job", "position", "hire", "hiring", "career", "apply", "application", "candidate"],
            "Support": ["support", "help", "issue", "problem", "bug", "error", "broken", "not working", "assistance"],
            "Legal": ["legal", "contract", "agreement", "nda", "terms", "law", "lawyer", "attorney", "compliance"],
            "Ops": ["operations", "ops", "logistics", "shipping", "delivery", "order", "fulfillment"],
            "Marketing": ["marketing", "promotion", "campaign", "advertisement", "ad", "newsletter", "event"]
        }
        
        # Intent keywords
        self.intent_keywords = {
            "Inquiry": ["interested", "inquiry", "question", "ask", "wondering", "curious", "information", "details"],
            "Follow-up": ["follow up", "following up", "checking in", "following", "update", "status"],
            "Objection": ["objection", "concern", "worried", "problem", "issue", "not sure", "hesitant", "doubt"],
            "Scheduling": ["schedule", "meeting", "call", "appointment", "calendar", "available", "time", "when"],
            "Application": ["apply", "application", "resume", "cv", "candidate", "position", "job"],
            "FAQ": ["faq", "frequently asked", "common question", "how to", "how do"],
            "Complaint": ["complaint", "unhappy", "dissatisfied", "poor", "bad", "terrible", "awful"]
        }
        
        # Urgency keywords
        self.urgency_keywords = {
            "Immediate": ["urgent", "asap", "as soon as possible", "immediately", "right away", "emergency", "critical"],
            "Soon": ["soon", "quickly", "fast", "prompt", "timely", "asap", "priority"]
        }
    
    def classify(self, subject: str, body: str) -> Dict[str, str]:
        """
        Classify email based on subject and body
        
        Returns:
            Dict with function, intent, urgency, impact, confidence
        """
        # Combine subject and body for analysis
        text = f"{subject} {body}".lower()
        
        # Classify function
        function = self._classify_function(text)
        
        # Classify intent
        intent = self._classify_intent(text)
        
        # Classify urgency
        urgency = self._classify_urgency(text)
        
        # Classify impact (based on function)
        impact = self._classify_impact(function)
        
        # Classify confidence
        confidence = self._classify_confidence(text, function, intent)
        
        return {
            "function": function,
            "intent": intent,
            "urgency": urgency,
            "impact": impact,
            "confidence": confidence
        }
    
    def _classify_function(self, text: str) -> str:
        """Classify email function"""
        scores = {}
        
        for func, keywords in self.function_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[func] = score
        
        if scores:
            # Return function with highest score
            return max(scores, key=scores.get)
        
        return "Admin"
    
    def _classify_intent(self, text: str) -> str:
        """Classify email intent"""
        scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[intent] = score
        
        if scores:
            # Return intent with highest score
            return max(scores, key=scores.get)
        
        return "Inquiry"
    
    def _classify_urgency(self, text: str) -> str:
        """Classify email urgency"""
        for urgency, keywords in self.urgency_keywords.items():
            if any(keyword in text for keyword in keywords):
                return urgency
        
        return "Can wait"
    
    def _classify_impact(self, function: str) -> str:
        """Classify email impact based on function"""
        impact_map = {
            "Sales": "Revenue",
            "Hiring": "Hiring",
            "Support": "Brand",
            "Legal": "Brand",
            "Ops": "Low",
            "Marketing": "Low",
            "Admin": "Low"
        }
        
        return impact_map.get(function, "Low")
    
    def _classify_confidence(self, text: str, function: str, intent: str) -> str:
        """Classify confidence level"""
        # Check if we found clear keywords
        function_found = function != "Admin"
        intent_found = intent != "Inquiry" or any(keyword in text for keyword in self.intent_keywords["Inquiry"])
        
        if function_found and intent_found:
            return "Clear"
        elif function_found or intent_found:
            return "Ambiguous"
        else:
            return "Missing info"


# Singleton instance
classification_agent = ClassificationAgent()

