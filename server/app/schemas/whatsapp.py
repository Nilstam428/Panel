from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class WhatsAppTextParameter(BaseModel):
    type: Literal["text"] = "text"
    text: str


class WhatsAppBodyComponent(BaseModel):
    type: Literal["body"] = "body"
    parameters: List[WhatsAppTextParameter]


class WhatsAppLanguage(BaseModel):
    code: str = "en_US"


class WhatsAppTemplatePayload(BaseModel):
    name: str
    language: WhatsAppLanguage = Field(default_factory=WhatsAppLanguage)
    components: List[WhatsAppBodyComponent]


class WhatsAppSendRequest(BaseModel):
    messaging_product: Literal["whatsapp"] = "whatsapp"
    recipient_type: Literal["individual"] = "individual"
    to: str
    type: Literal["template"] = "template"
    template: WhatsAppTemplatePayload


class WhatsAppContact(BaseModel):
    input: str
    wa_id: str


class WhatsAppMessageSuccessItem(BaseModel):
    id: str


class WhatsAppSendResponse(BaseModel):
    messaging_product: str = "whatsapp"
    contacts: List[WhatsAppContact] = Field(default_factory=list)
    messages: List[WhatsAppMessageSuccessItem] = Field(default_factory=list)


class WhatsAppErrorDetail(BaseModel):
    message: str
    type: Optional[str] = None
    code: Optional[int] = None
    error_subcode: Optional[int] = None
    fbtrace_id: Optional[str] = None


class WhatsAppErrorResponse(BaseModel):
    error: WhatsAppErrorDetail
