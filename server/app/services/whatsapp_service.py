import logging
import uuid
from typing import Optional, Protocol
import httpx
from app.config import Settings, get_settings
from app.schemas.whatsapp import (
    WhatsAppContact,
    WhatsAppErrorResponse,
    WhatsAppMessageSuccessItem,
    WhatsAppSendRequest,
    WhatsAppSendResponse,
    WhatsAppTemplatePayload,
)

logger = logging.getLogger("whatsapp_service")


class WhatsAppClientProtocol(Protocol):
    async def send_template(
        self,
        phone_number: str,
        template: WhatsAppTemplatePayload,
    ) -> WhatsAppSendResponse:
        ...


class MetaWhatsAppService:
    """Official Meta WhatsApp Business Cloud API Client."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def send_template(
        self,
        phone_number: str,
        template: WhatsAppTemplatePayload,
    ) -> WhatsAppSendResponse:
        # Sanitize recipient for WhatsApp API (no leading '+' for Meta's 'to' field)
        to_number = phone_number.lstrip("+").strip()

        request_payload = WhatsAppSendRequest(
            messaging_product="whatsapp",
            recipient_type="individual",
            to=to_number,
            type="template",
            template=template,
        )

        # Dry-run / Mock mode if enabled or if credentials are empty
        if not self.settings.is_configured_for_live:
            return self._simulate_send(to_number, request_payload)

        # Live Meta Cloud API Dispatch
        return await self._dispatch_meta_request(to_number, request_payload)

    def _simulate_send(
        self, to_number: str, request_payload: WhatsAppSendRequest
    ) -> WhatsAppSendResponse:
        simulated_id = f"wamid.HBgL{uuid.uuid4().hex[:20]}="
        logger.info(
            f"[DRY RUN SIMULATOR] Simulated WhatsApp message to {to_number[:4]}****{to_number[-2:]} "
            f"using template '{request_payload.template.name}'. Generated ID: {simulated_id}"
        )
        logger.debug(
            f"[DRY RUN SIMULATOR] Payload preview: {request_payload.model_dump_json(indent=2)}"
        )
        return WhatsAppSendResponse(
            messaging_product="whatsapp",
            contacts=[WhatsAppContact(input=to_number, wa_id=to_number)],
            messages=[WhatsAppMessageSuccessItem(id=simulated_id)],
        )

    async def _dispatch_meta_request(
        self, to_number: str, request_payload: WhatsAppSendRequest
    ) -> WhatsAppSendResponse:
        url = self.settings.messages_endpoint
        headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    content=request_payload.model_dump_json(),
                )
            except httpx.TimeoutException as exc:
                logger.error(f"WhatsApp API timeout when contacting Meta: {exc}")
                raise RuntimeError("WhatsApp API timeout when contacting Meta.") from exc
            except httpx.RequestError as exc:
                logger.error(f"WhatsApp API connection error: {exc}")
                raise RuntimeError("Failed to connect to Meta WhatsApp API.") from exc

        if response.status_code >= 400:
            self._handle_error_response(response)

        data = response.json()
        return WhatsAppSendResponse.model_validate(data)

    def _handle_error_response(self, response: httpx.Response) -> None:
        try:
            error_data = response.json()
            parsed_error = WhatsAppErrorResponse.model_validate(error_data)
            err_msg = parsed_error.error.message
            err_code = parsed_error.error.code
            logger.error(
                f"Meta WhatsApp API returned error code {err_code}: {err_msg} (status {response.status_code})"
            )
            raise ValueError(f"Meta WhatsApp Error: {err_msg} (Code {err_code})")
        except ValueError:
            raise
        except Exception:
            logger.error(
                f"Meta WhatsApp API error with status {response.status_code}: {response.text}"
            )
            raise ValueError(
                f"Meta WhatsApp API request failed with status {response.status_code}"
            )


from fastapi import Depends

def get_whatsapp_service(
    settings: Settings = Depends(get_settings),
) -> MetaWhatsAppService:
    return MetaWhatsAppService(settings=settings)

