"""
AI-assisted draft editing service.
Uses the internal LLM to edit draft subject and body based on user instructions.
Brand-context aware: when brand_context is provided (from Redis/Drive), the LLM
adheres to the company's voice, tone, and policies when editing.
"""
from services.openai_client import openai_client
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Safe max length for body to avoid oversized responses
MAX_BODY_LENGTH = 50_000

# Max chars of brand context to include in prompt (avoid token overflow)
MAX_VOICE_CHARS = 2000
MAX_POLICIES_CHARS = 800
MAX_COMPANY_CHARS = 500

BASE_SYSTEM_RULES = """You are an email draft editor. Apply the user's editing instruction to the draft.

Rules:
1. Apply only the user's instruction; preserve intent and structure unless the instruction says otherwise.
2. Do not add new facts, make up information, or hallucinate.
3. Output only valid JSON with exactly two keys: "subject" (string) and "body" (string). No markdown, no commentary, no other keys."""


def _build_brand_section(brand_context: Dict[str, Any]) -> str:
    """Build BRAND GUIDELINES section from company brand context (full + key_points)."""
    if not brand_context or not isinstance(brand_context, dict):
        return ""
    full = brand_context.get("full") or {}
    if not isinstance(full, dict):
        return ""
    parts = []
    voice = full.get("voice") or ""
    if voice:
        voice_trunc = voice[:MAX_VOICE_CHARS] + ("..." if len(voice) > MAX_VOICE_CHARS else "")
        parts.append(f"BRAND VOICE AND TONE (follow when editing):\n{voice_trunc}")
    policies = full.get("policies") or ""
    if policies:
        policies_trunc = policies[:MAX_POLICIES_CHARS] + ("..." if len(policies) > MAX_POLICIES_CHARS else "")
        parts.append(f"COMPANY POLICIES (respect when editing):\n{policies_trunc}")
    company = full.get("company") or ""
    if company:
        company_trunc = company[:MAX_COMPANY_CHARS] + ("..." if len(company) > MAX_COMPANY_CHARS else "")
        parts.append(f"COMPANY CONTEXT:\n{company_trunc}")
    if not parts:
        return ""
    return "\n\n---\n\nBRAND GUIDELINES (apply these when editing the draft):\n\n" + "\n\n".join(parts)


def _build_user_message(subject: str, body: str, instruction: str) -> str:
    return f"""Draft subject:
{subject}

Draft body:
{body}

Instruction:
{instruction}"""


async def edit_draft_with_ai(
    subject: str,
    body: str,
    instruction: str,
    brand_context: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Edit draft subject and body using the LLM based on user instruction.
    When brand_context is provided (from Redis/Drive), the model follows
    the company's brand voice and policies when editing.

    Args:
        subject: Current draft subject.
        body: Current draft body.
        instruction: Natural language editing instruction from the user.
        brand_context: Optional dict from brand_context_loader (structure:
            {"full": {voice, policies, company, ...}, "key_points": {...}}).
            Loaded via Redis cache; same source as LangGraph flows.

    Returns:
        Tuple of (edited_subject, edited_body).

    Raises:
        ValueError: If instruction is empty, or LLM response is invalid/missing keys.
    """
    instruction = (instruction or "").strip()
    if not instruction:
        raise ValueError("Instruction is required and cannot be empty")

    system_content = BASE_SYSTEM_RULES
    brand_section = _build_brand_section(brand_context or {})
    if brand_section:
        system_content += brand_section
        logger.info("Edit with AI: using company brand context for this edit")

    user_content = _build_user_message(subject, body, instruction)
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

    response = await openai_client.chat_completion(
        messages=messages,
        temperature=0.5,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    data = openai_client.parse_json_response(response)
    if not isinstance(data, dict):
        raise ValueError("LLM did not return a JSON object")

    # Case-insensitive key lookup (LLM may return "Subject"/"Body")
    key_lower = {k.lower(): k for k in data.keys()}
    edited_subject = data.get(key_lower.get("subject", "subject")) if "subject" in key_lower else data.get("subject")
    edited_body = data.get(key_lower.get("body", "body")) if "body" in key_lower else data.get("body")
    if edited_subject is None or edited_body is None:
        raise ValueError("LLM response must contain both 'subject' and 'body'")

    edited_subject = str(edited_subject).strip()
    edited_body = str(edited_body).strip()
    if not edited_subject:
        raise ValueError("Edited subject cannot be empty")
    if not edited_body:
        raise ValueError("Edited body cannot be empty")

    if len(edited_body) > MAX_BODY_LENGTH:
        edited_body = edited_body[:MAX_BODY_LENGTH]
        logger.warning(f"Truncated AI-edited body to {MAX_BODY_LENGTH} chars")

    return edited_subject, edited_body
