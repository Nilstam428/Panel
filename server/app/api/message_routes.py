import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.config import Settings, get_settings
from app.schemas.message import (
    MessagePreviewRequest,
    MessagePreviewResponse,
    SendMessageRequest,
    SendMessageResponse,
    TemplateInfoResponse,
)
from app.services.template_service import TemplateService
from app.services.whatsapp_service import MetaWhatsAppService, get_whatsapp_service

logger = logging.getLogger("message_routes")

router = APIRouter(prefix="/api", tags=["Messages & Templates"])


def get_template_service() -> TemplateService:
    return TemplateService()


@router.get(
    "/templates",
    response_model=List[TemplateInfoResponse],
    summary="List available message templates",
    description="Retrieve all registered approved WhatsApp message templates with their metadata and fields.",
)
def list_templates(
    service: TemplateService = Depends(get_template_service),
) -> List[TemplateInfoResponse]:
    return service.get_available_templates()


@router.post(
    "/messages/preview",
    response_model=MessagePreviewResponse,
    summary="Preview rendered template text",
    description="Render the message text using provided variable values for admin verification prior to sending.",
)
def preview_message(
    payload: MessagePreviewRequest,
    service: TemplateService = Depends(get_template_service),
) -> MessagePreviewResponse:
    try:
        rendered, params = service.preview_template(
            payload.template_name, payload.parameters
        )
        return MessagePreviewResponse(
            template_name=payload.template_name,
            rendered_text=rendered,
            parameters=params,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/messages/send",
    response_model=SendMessageResponse,
    summary="Send WhatsApp notification",
    description="Validate input, construct WhatsApp Cloud API payload, and send to the customer via Meta Cloud API.",
)
async def send_message(
    payload: SendMessageRequest,
    template_service: TemplateService = Depends(get_template_service),
    whatsapp_service: MetaWhatsAppService = Depends(get_whatsapp_service),
    settings: Settings = Depends(get_settings),
) -> SendMessageResponse:
    # 1. Build and validate template payload
    try:
        template_payload, rendered_text = template_service.build_meta_payload(
            payload.template_name, payload.parameters
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 2. Dispatch via WhatsApp service (Live or Dry-Run Simulator)
    try:
        response = await whatsapp_service.send_template(
            phone_number=payload.phone_number,
            template=template_payload,
        )
        msg_id = (
            response.messages[0].id if response.messages else "wamid.UNKNOWN"
        )
        is_dry_run = not settings.is_configured_for_live

        return SendMessageResponse(
            success=True,
            message_id=msg_id,
            phone_number=payload.phone_number,
            template_name=payload.template_name,
            rendered_text=rendered_text,
            dry_run=is_dry_run,
        )
    except ValueError as exc:
        logger.warning(f"Validation or Meta API error during send: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Internal error sending message: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send WhatsApp message via Meta Cloud API.",
        )
