"""
Parse follow-up rules from company PLAYBOOKS.md (from Brand Context / Google Drive).

Used to set Next_Followup_Date after outbound email sent:
e.g. "Day 3-5 | Soft bump" -> 3 days after send date.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Default days to next follow-up if playbook not found or not parseable (PLAYBOOKS: "Day 3-5")
DEFAULT_FOLLOWUP_DAYS = 3


def parse_followup_days_after_outreach(playbooks_content: Optional[str]) -> int:
    """
    Parse follow-up cadence from PLAYBOOKS.md for "After Initial Outreach (No Response)".

    Looks for section like:
        ## Follow-Up Cadence
        ### After Initial Outreach (No Response)
        | Day | Action |
        | 3-5 | Soft bump on same channel |

    Returns the first day number (e.g. 3 for "Day 3-5"). Default 3 if not found.
    """
    if not playbooks_content or not playbooks_content.strip():
        logger.info("No playbooks content; using default follow-up days %s", DEFAULT_FOLLOWUP_DAYS)
        return DEFAULT_FOLLOWUP_DAYS

    # Look for "Day N" or "Day N-M" in context of follow-up / outreach
    # Common patterns: "Day 3-5", "Day 3", "| 3-5 |"
    text = playbooks_content
    # Prefer "After Initial Outreach" or "Follow-Up Cadence" section
    outreach_section = None
    if "After Initial Outreach" in text:
        try:
            start = text.index("After Initial Outreach")
            end = text.find("###", start + 5)
            if end == -1:
                end = text.find("## ", start + 5)
            if end == -1:
                end = len(text)
            outreach_section = text[start:end]
        except ValueError:
            pass
    if not outreach_section and "Follow-Up Cadence" in text:
        try:
            start = text.index("Follow-Up Cadence")
            end = min(
                text.find("## ", start + 5) if text.find("## ", start + 5) != -1 else len(text),
                text.find("# What NOT", start + 5) if text.find("# What NOT", start + 5) != -1 else len(text),
            )
            outreach_section = text[start:end]
        except ValueError:
            pass
    search_text = outreach_section if outreach_section else text

    # Match "Day 3-5" or "| 3-5 |" or "Day 3"
    match = re.search(r"Day\s+(\d+)(?:-\d+)?", search_text, re.IGNORECASE)
    if match:
        days = int(match.group(1))
        if 1 <= days <= 90:
            logger.info("Parsed follow-up days from playbook: %s", days)
            return days
    match = re.search(r"\|\s*(\d+)(?:-\d+)?\s*\|", search_text)
    if match:
        days = int(match.group(1))
        if 1 <= days <= 90:
            logger.info("Parsed follow-up days from playbook table: %s", days)
            return days

    logger.info("Could not parse follow-up days from playbook; using default %s", DEFAULT_FOLLOWUP_DAYS)
    return DEFAULT_FOLLOWUP_DAYS
