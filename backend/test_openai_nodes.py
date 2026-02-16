"""
Test script to verify OpenAI API key and model are being used correctly
Run this to test all Flow 1 nodes
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from services.openai_client import openai_client
from services.flow1.state import Flow1State
from services.flow1.nodes.classification_node import classification_node
from services.flow1.nodes.priority_scorer_node import priority_scorer_node
from services.flow1.nodes.summarizer_node import summarizer_node
from services.flow1.nodes.action_recommender_node import action_recommender_node
from services.flow1.nodes.draft_generator_node import draft_generator_node
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_openai_config():
    """Test OpenAI client configuration"""
    print("\n" + "="*60)
    print("TEST 1: OpenAI Configuration")
    print("="*60)
    
    print(f"[OK] OPENAI_API_KEY: {'Set' if settings.OPENAI_API_KEY else 'NOT SET'}")
    if settings.OPENAI_API_KEY:
        print(f"  Key preview: {settings.OPENAI_API_KEY[:20]}...{settings.OPENAI_API_KEY[-10:]}")
    
    print(f"[OK] OPENAI_MODEL: {settings.OPENAI_MODEL}")
    print(f"[OK] OpenAI Client Model: {openai_client.model}")
    
    if openai_client.model != settings.OPENAI_MODEL:
        print(f"[WARNING] Client model ({openai_client.model}) doesn't match config ({settings.OPENAI_MODEL})")
    else:
        print("[OK] Model configuration matches!")
    
    # Test simple API call
    try:
        test_response = await openai_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            temperature=0.3,
            max_tokens=50
        )
        print(f"[OK] API Test Response: {test_response.strip()}")
        print("[OK] OpenAI API is working correctly!")
        return True
    except Exception as e:
        print(f"[FAIL] API Test Failed: {str(e)}")
        return False


async def test_classification_node():
    """Test classification node"""
    print("\n" + "="*60)
    print("TEST 2: Classification Node")
    print("="*60)
    
    test_state = Flow1State(
        company_id="test-company-id",
        email_subject="Enterprise Pricing Inquiry",
        email_body="Hi, I'm reaching out on behalf of TechCorp Inc. We're interested in your platform for our team of 50+ employees. Could you please provide enterprise pricing details?",
        from_email="test@example.com",
        to_email="company@example.com",
        thread_id=None,
        gmail_message_id=None,
        thread_history=[],
        thread_count=0,
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
        email_id=None,
        draft_id=None,
        status="processing",
        error_message=None
    )
    
    try:
        result = await classification_node(test_state)
        print(f"[OK] Classification Result:")
        print(f"  Function: {result.get('function')}")
        print(f"  Intent: {result.get('intent')}")
        print(f"  Urgency: {result.get('urgency')}")
        print(f"  Impact: {result.get('impact')}")
        print(f"  Confidence: {result.get('confidence')}")
        
        # Verify it's not defaulting to Admin
        if result.get('function') == 'Sales':
            print("[OK] Correctly classified as Sales (not Admin)!")
        else:
            print(f"[WARNING] Classified as {result.get('function')} - expected Sales for pricing inquiry")
        
        return result
    except Exception as e:
        print(f"[FAIL] Classification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_priority_scorer_node(classification_result):
    """Test priority scorer node"""
    print("\n" + "="*60)
    print("TEST 3: Priority Scorer Node")
    print("="*60)
    
    if not classification_result:
        print("[SKIP] Skipping - no classification result")
        return None
    
    test_state = Flow1State(
        company_id="test-company-id",
        email_subject="Enterprise Pricing Inquiry",
        email_body="Test email",
        from_email="test@example.com",
        to_email="company@example.com",
        thread_id=None,
        gmail_message_id=None,
        thread_history=[],
        thread_count=0,
        function=classification_result.get('function'),
        intent=classification_result.get('intent'),
        urgency=classification_result.get('urgency'),
        impact=classification_result.get('impact'),
        confidence=classification_result.get('confidence'),
        classification_metadata=classification_result.get('classification_metadata'),
        priority_score=None,
        executive_summary=None,
        recommended_action=None,
        draft_subject=None,
        draft_body=None,
        template_used=None,
        variables_used=None,
        email_id=None,
        draft_id=None,
        status="processing",
        error_message=None
    )
    
    try:
        result = await priority_scorer_node(test_state)
        score = result.get('priority_score')
        print(f"[OK] Priority Score: {score}")
        
        if score == 50:
            print("[WARNING] Score is 50 (default) - may not be calculating correctly")
        elif score < 20 or score > 100:
            print(f"[WARNING] Score {score} is outside expected range (0-100)")
        else:
            print(f"[OK] Score looks reasonable: {score}")
        
        return result
    except Exception as e:
        print(f"[FAIL] Priority scoring failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_summarizer_node(classification_result):
    """Test summarizer node"""
    print("\n" + "="*60)
    print("TEST 4: Summarizer Node")
    print("="*60)
    
    if not classification_result:
        print("[SKIP] Skipping - no classification result")
        return None
    
    test_state = Flow1State(
        company_id="test-company-id",
        email_subject="Enterprise Pricing Inquiry",
        email_body="Hi, I'm reaching out on behalf of TechCorp Inc. We're interested in your platform for our team of 50+ employees. Could you please provide enterprise pricing details?",
        from_email="test@example.com",
        to_email="company@example.com",
        thread_id=None,
        gmail_message_id=None,
        thread_history=[],
        thread_count=0,
        function=classification_result.get('function'),
        intent=classification_result.get('intent'),
        urgency=classification_result.get('urgency'),
        impact=classification_result.get('impact'),
        confidence=classification_result.get('confidence'),
        classification_metadata=classification_result.get('classification_metadata'),
        priority_score=None,
        executive_summary=None,
        recommended_action=None,
        draft_subject=None,
        draft_body=None,
        template_used=None,
        variables_used=None,
        email_id=None,
        draft_id=None,
        status="processing",
        error_message=None
    )
    
    try:
        result = await summarizer_node(test_state)
        summary = result.get('executive_summary')
        print(f"[OK] Executive Summary: {summary}")
        print(f"  Length: {len(summary)} characters")
        
        if "the email says" in summary.lower() or "they wrote" in summary.lower():
            print("[WARNING] Summary contains content-focused phrases")
        else:
            print("[OK] Summary appears meaning-focused")
        
        return result
    except Exception as e:
        print(f"[FAIL] Summarization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_action_recommender_node(classification_result):
    """Test action recommender node"""
    print("\n" + "="*60)
    print("TEST 5: Action Recommender Node")
    print("="*60)
    
    if not classification_result:
        print("[SKIP] Skipping - no classification result")
        return None
    
    test_state = Flow1State(
        company_id="test-company-id",
        email_subject="Enterprise Pricing Inquiry",
        email_body="Test email",
        from_email="test@example.com",
        to_email="company@example.com",
        thread_id=None,
        gmail_message_id=None,
        thread_history=[],
        thread_count=0,
        function=classification_result.get('function'),
        intent=classification_result.get('intent'),
        urgency=classification_result.get('urgency'),
        impact=classification_result.get('impact'),
        confidence=classification_result.get('confidence'),
        classification_metadata=classification_result.get('classification_metadata'),
        priority_score=None,
        executive_summary=None,
        recommended_action=None,
        draft_subject=None,
        draft_body=None,
        template_used=None,
        variables_used=None,
        email_id=None,
        draft_id=None,
        status="processing",
        error_message=None
    )
    
    try:
        result = await action_recommender_node(test_state)
        action = result.get('recommended_action')
        print(f"[OK] Recommended Action: {action}")
        
        valid_actions = ["Reply with template", "Ask for missing information", "Schedule meeting", 
                        "Review resume", "Escalate to human", "Hold/Ignore"]
        if action in valid_actions:
            print("[OK] Action is valid")
        else:
            print(f"[WARNING] Action '{action}' not in valid actions list")
        
        return result
    except Exception as e:
        print(f"[FAIL] Action recommendation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_draft_generator_node(classification_result, action_result):
    """Test draft generator node"""
    print("\n" + "="*60)
    print("TEST 6: Draft Generator Node")
    print("="*60)
    
    if not classification_result or not action_result:
        print("[SKIP] Skipping - missing previous results")
        return None
    
    test_state = Flow1State(
        company_id="test-company-id",
        email_subject="Enterprise Pricing Inquiry",
        email_body="Hi, I'm reaching out on behalf of TechCorp Inc. We're interested in your platform for our team of 50+ employees. Could you please provide: 1. Enterprise pricing details 2. Feature comparison 3. Available integrations 4. Implementation timeline",
        from_email="test@example.com",
        to_email="company@example.com",
        thread_id=None,
        gmail_message_id=None,
        thread_history=[],
        thread_count=0,
        function=classification_result.get('function'),
        intent=classification_result.get('intent'),
        urgency=classification_result.get('urgency'),
        impact=classification_result.get('impact'),
        confidence=classification_result.get('confidence'),
        classification_metadata=classification_result.get('classification_metadata'),
        priority_score=None,
        executive_summary=None,
        recommended_action=action_result.get('recommended_action'),
        draft_subject=None,
        draft_body=None,
        template_used=None,
        variables_used=None,
        email_id=None,
        draft_id=None,
        status="processing",
        error_message=None
    )
    
    try:
        result = await draft_generator_node(test_state, config={})
        draft_body = result.get('draft_body')
        
        if not draft_body:
            print("[SKIP] No draft generated (may be expected for some actions)")
            return result
        
        print(f"[OK] Draft Generated:")
        print(f"  Subject: {result.get('draft_subject')}")
        print(f"  Body length: {len(draft_body)} characters")
        print(f"  Template used: {result.get('template_used')}")
        print(f"\n  Draft preview (first 300 chars):")
        print(f"  {draft_body[:300]}...")
        
        # Check if it's the generic fallback
        if "Thank you for your email. We'll get back to you soon" in draft_body:
            print("[WARNING] Draft appears to be generic fallback")
        elif len(draft_body) < 100:
            print("[WARNING] Draft is very short")
        else:
            print("[OK] Draft looks substantial and specific!")
        
        return result
    except Exception as e:
        print(f"[FAIL] Draft generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_thread_context():
    """Test thread context feature"""
    print("\n" + "="*60)
    print("TEST 7: Thread Context Feature")
    print("="*60)
    
    # Create mock thread history
    mock_thread_history = [
        {
            "subject": "Enterprise Pricing Inquiry",
            "body": "Hi, I'm reaching out on behalf of TechCorp. We're interested in your platform for 50+ employees. Could you provide pricing details?",
            "from_email": "sarah@techcorp.com",
            "created_at": "2026-02-10T10:00:00",
            "was_reply": False
        },
        {
            "subject": "Re: Enterprise Pricing Inquiry",
            "body": "Thank you for your interest! I've attached our enterprise pricing guide. Would you like to schedule a call to discuss your specific needs?",
            "from_email": "company@example.com",
            "created_at": "2026-02-10T14:00:00",
            "was_reply": True
        }
    ]
    
    # Test classification with thread context
    test_state = Flow1State(
        company_id="test-company-id",
        email_subject="Re: Enterprise Pricing Inquiry",
        email_body="Thanks for the pricing guide. We have a few questions: 1. Do you offer volume discounts for 100+ users? 2. What's the implementation timeline? 3. Can we integrate with Salesforce?",
        from_email="sarah@techcorp.com",
        to_email="company@example.com",
        thread_id="thread_123",
        gmail_message_id=None,
        thread_history=mock_thread_history,
        thread_count=2,
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
        email_id=None,
        draft_id=None,
        status="processing",
        error_message=None
    )
    
    try:
        # Test classification with thread context
        classification_result = await classification_node(test_state)
        print(f"[OK] Classification with Thread Context:")
        print(f"  Function: {classification_result.get('function')}")
        print(f"  Intent: {classification_result.get('intent')}")
        
        # Check if it detected follow-up
        if classification_result.get('intent') == 'Follow-up':
            print("[OK] Correctly detected Follow-up intent with thread context!")
        else:
            print(f"[WARNING] Intent is {classification_result.get('intent')} - expected Follow-up")
        
        # Update state with classification
        test_state.update(classification_result)
        
        # Test draft generation with thread context
        draft_result = await draft_generator_node(test_state, config={})
        draft_body = draft_result.get('draft_body')
        
        if draft_body:
            print(f"[OK] Draft Generated with Thread Context:")
            print(f"  Length: {len(draft_body)} characters")
            print(f"  Preview: {draft_body[:200]}...")
            
            # Check if draft references previous conversation
            if any(word in draft_body.lower() for word in ['pricing guide', 'previous', 'earlier', 'as mentioned', 'discussed']):
                print("[OK] Draft appears to reference previous conversation!")
            else:
                print("[WARNING] Draft may not reference previous conversation")
        else:
            print("[SKIP] No draft generated")
        
        return {"classification": classification_result, "draft": draft_result}
        
    except Exception as e:
        print(f"[FAIL] Thread context test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FLOW 1 NODES - OPENAI API TEST")
    print("="*60)
    print(f"Testing with model: {settings.OPENAI_MODEL}")
    print(f"API Key: {'Set' if settings.OPENAI_API_KEY else 'NOT SET'}")
    
    # Test 1: Configuration
    config_ok = await test_openai_config()
    if not config_ok:
        print("\n[FAIL] Configuration test failed. Cannot proceed with node tests.")
        return
    
    # Test 2: Classification
    classification_result = await test_classification_node()
    
    # Test 3: Priority Scorer
    priority_result = await test_priority_scorer_node(classification_result)
    
    # Test 4: Summarizer
    summary_result = await test_summarizer_node(classification_result)
    
    # Test 5: Action Recommender
    action_result = await test_action_recommender_node(classification_result)
    
    # Test 6: Draft Generator
    draft_result = await test_draft_generator_node(classification_result, action_result)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"[OK] Configuration: {'PASS' if config_ok else 'FAIL'}")
    print(f"[OK] Classification: {'PASS' if classification_result else 'FAIL'}")
    print(f"[OK] Priority Scorer: {'PASS' if priority_result else 'FAIL'}")
    print(f"[OK] Summarizer: {'PASS' if summary_result else 'FAIL'}")
    print(f"[OK] Action Recommender: {'PASS' if action_result else 'FAIL'}")
    print(f"[OK] Draft Generator: {'PASS' if draft_result else 'FAIL'}")
    print(f"[OK] Thread Context: {'PASS' if thread_result else 'FAIL'}")
    
    all_passed = all([
        config_ok,
        classification_result,
        priority_result,
        summary_result,
        action_result,
        draft_result,
        thread_result
    ])
    
    if all_passed:
        print("\n[SUCCESS] All tests passed! OpenAI API and nodes are working correctly.")
    else:
        print("\n[WARNING] Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())

