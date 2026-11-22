from typing import Dict, List
from app.schemas.message import TemplateFieldMeta
from app.templates.base import BaseWhatsAppTemplate


class VehiclePUCCExpiryTemplate(BaseWhatsAppTemplate):
    name = "vehicle_pucc_expiry"
    title = "Vehicle PUCC Expiry"
    description = "Notifies customer regarding upcoming Pollution Under Control Certificate (PUCC) expiration."
    language_code = "en_US"

    fields = [
        TemplateFieldMeta(
            name="person_name",
            label="Customer Name",
            placeholder="e.g. SHUBHAM TAMBOLI",
            field_type="text",
            required=True,
            example="SHUBHAM TAMBOLI",
        ),
        TemplateFieldMeta(
            name="vehicle_number",
            label="Vehicle Number",
            placeholder="e.g. RJ14GG9920",
            field_type="text",
            required=True,
            example="RJ14GG9920",
        ),
        TemplateFieldMeta(
            name="expiry_date",
            label="Expiry Date",
            placeholder="e.g. 23-Jun-2026",
            field_type="date",
            required=True,
            example="23-Jun-2026",
        ),
    ]

    def build_parameters(self, params: Dict[str, str]) -> List[str]:
        cleaned = self.validate_fields(params)
        # WhatsApp variable ordering: {{1}}=person_name, {{2}}=vehicle_number, {{3}}=expiry_date
        return [
            cleaned["person_name"],
            cleaned["vehicle_number"],
            cleaned["expiry_date"],
        ]

    def render_preview(self, params: Dict[str, str]) -> str:
        name = params.get("person_name", "{{1}}") or "{{1}}"
        vehicle = params.get("vehicle_number", "{{2}}") or "{{2}}"
        expiry = params.get("expiry_date", "{{3}}") or "{{3}}"
        return (
            f"Kind Attention {name}\n\n"
            f"Pollution Under Control Certificate (PUCC) of Vehicle No. {vehicle} will expire on {expiry}.\n\n"
            "Kindly renew the certificate before the expiry date to avoid penal actions as per law.\n\n"
            "Thanks. MoRTH"
        )
