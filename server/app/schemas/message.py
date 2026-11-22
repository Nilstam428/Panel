import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


def normalize_phone_number(v: str) -> str:
    """Normalizes phone number to E.164 format (defaulting to +91 if 10 digits given)."""
    cleaned = re.sub(r"[^\d+]", "", v.strip())
    if not cleaned:
        raise ValueError("Phone number cannot be empty")

    # If starts with +, remove + to inspect digits
    if cleaned.startswith("+"):
        digits = cleaned[1:]
    elif cleaned.startswith("0"):
        digits = cleaned[1:]
    else:
        digits = cleaned

    if len(digits) == 10:
        # Default Indian 10-digit mobile number
        return f"+91{digits}"
    elif len(digits) >= 11 and len(digits) <= 15:
        return f"+{digits}"
    else:
        raise ValueError(
            f"Invalid phone number format. Expected 10-digit mobile or full international number, got '{v}'"
        )


class TemplateFieldMeta(BaseModel):
    name: str
    label: str
    placeholder: str = ""
    field_type: str = "text"  # text, date, etc.
    required: bool = True
    example: str = ""


class TemplateInfoResponse(BaseModel):
    name: str
    title: str
    description: str
    language_code: str = "en_US"
    fields: List[TemplateFieldMeta]
    sample_preview: str


class MessagePreviewRequest(BaseModel):
    template_name: str
    parameters: Dict[str, str] = Field(default_factory=dict)


class MessagePreviewResponse(BaseModel):
    template_name: str
    rendered_text: str
    parameters: List[str]  # ordered WhatsApp parameters {{1}}, {{2}}, ...


class SendMessageRequest(BaseModel):
    phone_number: str
    template_name: str
    parameters: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value pairs matching the template's required fields",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone_number(v)


class SendMessageResponse(BaseModel):
    success: bool
    message_id: str
    phone_number: str
    template_name: str
    rendered_text: str
    dry_run: bool = False
    details: Optional[Dict[str, Any]] = None
