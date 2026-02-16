"""
Test script to verify thread_id and thread_history functionality
"""
import asyncio
import sys
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.email import Email
from models.company import Company
from services.flow1 import Flow1Orchestrator
from sqlalchemy import select
from datetime import datetime

async def test_thread_context():
    """Test that thread_id is maintained and thread_history is loaded correctly"""
    
    print("=" * 80)
    print("TESTING THREAD CONTEXT FUNCTIONALITY")
    print("=" * 80)
    
    # Get database session
    async for db in get_db():
        try:
            # Step 1: Find or create a test company
            print("\n[1] Finding test company...")
            result = await db.execute(
                select(Company).limit(1)
            )
            company = result.scalar_one_or_none()
            
            if not company:
                print("[FAIL] No company found in database. Please create a company first.")
                return False
            
            company_id = str(company.company_id)
            print(f"[OK] Using company: {company.name} (ID: {company_id})")
            
            # Step 2: Create a test thread with multiple emails
            print("\n[2] Creating test email thread...")
            test_thread_id = f"test_thread_{datetime.now().timestamp()}"
            
            # Email 1: Initial inquiry
            email1_data = {
                "subject": "Initial Inquiry - Pricing Question",
                "body": "Hello, I'm interested in your platform. Can you provide pricing information for 50 users?",
                "from": "customer@example.com",
                "to": company.email,
                "thread_id": test_thread_id,
                "gmail_message_id": f"test_msg_1_{datetime.now().timestamp()}"
            }
            
            orchestrator = Flow1Orchestrator()
            result1 = await orchestrator.process_email(
                db=db,
                company_id=company_id,
                email_data=email1_data
            )
            
            if not result1.get("email_id"):
                print(f"[FAIL] Failed to process first email: {result1}")
                return False
            
            email1_id = result1["email_id"]
            print(f"[OK] Email 1 created: {email1_id}")
            print(f"  Subject: {email1_data['subject']}")
            print(f"  Thread ID: {test_thread_id}")
            
            # Wait a bit to ensure different timestamps
            await asyncio.sleep(1)
            
            # Email 2: Follow-up in same thread
            email2_data = {
                "subject": "Re: Initial Inquiry - Pricing Question",
                "body": "Hi, I sent an email last week about pricing. Just following up - do you have any updates?",
                "from": "customer@example.com",
                "to": company.email,
                "thread_id": test_thread_id,  # Same thread_id
                "gmail_message_id": f"test_msg_2_{datetime.now().timestamp()}"
            }
            
            result2 = await orchestrator.process_email(
                db=db,
                company_id=company_id,
                email_data=email2_data
            )
            
            if not result2.get("email_id"):
                print(f"❌ Failed to process second email: {result2}")
                return False
            
            email2_id = result2["email_id"]
            print(f"[OK] Email 2 created: {email2_id}")
            print(f"  Subject: {email2_data['subject']}")
            print(f"  Thread ID: {test_thread_id}")
            
            # Step 3: Verify thread_id is stored correctly
            print("\n[3] Verifying thread_id storage...")
            result = await db.execute(
                select(Email).where(Email.id == UUID(email1_id))
            )
            email1_record = result.scalar_one_or_none()
            
            result = await db.execute(
                select(Email).where(Email.id == UUID(email2_id))
            )
            email2_record = result.scalar_one_or_none()
            
            if email1_record.thread_id != test_thread_id:
                print(f"[FAIL] Email 1 thread_id mismatch: expected {test_thread_id}, got {email1_record.thread_id}")
                return False
            
            if email2_record.thread_id != test_thread_id:
                print(f"[FAIL] Email 2 thread_id mismatch: expected {test_thread_id}, got {email2_record.thread_id}")
                return False
            
            print(f"[OK] Both emails have correct thread_id: {test_thread_id}")
            
            # Step 4: Test thread_history loading
            print("\n[4] Testing thread_history loading...")
            thread_history = await orchestrator._load_thread_history(
                db=db,
                company_id=company_id,
                thread_id=test_thread_id,
                current_gmail_message_id=email2_data["gmail_message_id"]
            )
            
            if len(thread_history) != 1:
                print(f"[FAIL] Expected 1 previous email in thread_history, got {len(thread_history)}")
                print(f"   Thread history: {thread_history}")
                return False
            
            if thread_history[0]["subject"] != email1_data["subject"]:
                print(f"[FAIL] Thread history subject mismatch: expected '{email1_data['subject']}', got '{thread_history[0]['subject']}'")
                return False
            
            print(f"[OK] Thread history loaded correctly:")
            print(f"  - Found {len(thread_history)} previous email(s)")
            print(f"  - Previous email subject: {thread_history[0]['subject']}")
            print(f"  - Previous email from: {thread_history[0]['from_email']}")
            
            # Step 5: Test that thread_history is used in state initialization
            print("\n[5] Testing thread_history in state initialization...")
            email3_data = {
                "subject": "Re: Re: Initial Inquiry - Pricing Question",
                "body": "Thanks for the information. I have a few more questions about the features.",
                "from": "customer@example.com",
                "to": company.email,
                "thread_id": test_thread_id,
                "gmail_message_id": f"test_msg_3_{datetime.now().timestamp()}"
            }
            
            initial_state = await orchestrator._initialize_state(
                company_id=company_id,
                email_data=email3_data,
                db=db
            )
            
            if initial_state.get("thread_count") != 2:
                print(f"[FAIL] Expected thread_count=2, got {initial_state.get('thread_count')}")
                return False
            
            if len(initial_state.get("thread_history", [])) != 2:
                print(f"[FAIL] Expected 2 emails in thread_history, got {len(initial_state.get('thread_history', []))}")
                return False
            
            print(f"[OK] State initialization includes thread context:")
            print(f"  - thread_count: {initial_state.get('thread_count')}")
            print(f"  - thread_history length: {len(initial_state.get('thread_history', []))}")
            print(f"  - Previous emails:")
            for i, prev in enumerate(initial_state.get("thread_history", []), 1):
                print(f"    {i}. {prev.get('subject', 'N/A')} (from: {prev.get('from_email', 'N/A')})")
            
            # Step 6: Verify thread_history is used in draft generation
            print("\n[6] Testing draft generation with thread context...")
            # Process email 3 to see if draft references previous emails
            result3 = await orchestrator.process_email(
                db=db,
                company_id=company_id,
                email_data=email3_data
            )
            
            if result3.get("draft_id"):
                # Get the draft
                from models.draft import Draft
                draft_result = await db.execute(
                    select(Draft).where(Draft.id == UUID(result3["draft_id"]))
                )
                draft = draft_result.scalar_one_or_none()
                
                if draft:
                    draft_body = draft.body.lower()
                    # Check if draft references previous conversation
                    has_context = any(keyword in draft_body for keyword in [
                        "pricing", "information", "following up", "previous", "earlier", "last week"
                    ])
                    
                    if has_context:
                        print(f"[OK] Draft appears to reference previous conversation")
                        print(f"  Draft preview: {draft.body[:200]}...")
                    else:
                        print(f"[WARN] Draft may not reference previous conversation (check manually)")
                        print(f"  Draft preview: {draft.body[:200]}...")
            
            print("\n" + "=" * 80)
            print("[SUCCESS] ALL THREAD CONTEXT TESTS PASSED!")
            print("=" * 80)
            print("\nSummary:")
            print(f"  [OK] thread_id is stored correctly: {test_thread_id}")
            print(f"  [OK] thread_history loads previous emails: {len(thread_history)} email(s)")
            print(f"  [OK] thread_count is calculated correctly: {initial_state.get('thread_count')}")
            print(f"  [OK] State includes thread_history for AI context")
            
            return True
            
        except Exception as e:
            print(f"\n[FAIL] TEST FAILED WITH ERROR:")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await db.close()

if __name__ == "__main__":
    success = asyncio.run(test_thread_context())
    sys.exit(0 if success else 1)

