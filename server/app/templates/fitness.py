from typing import Dict, List
from app.schemas.message import TemplateFieldMeta
from app.templates.base import BaseWhatsAppTemplate


class VehicleFitnessExpiryTemplate(BaseWhatsAppTemplate):
    name = "vehicle_fitness_expiry"
    title = "Vehicle Fitness Certificate Expiry"
    description = "Notifies customer regarding upcoming Fitness Certificate expiration."
    language_code = "en_US"

    fields = [
        TemplateFieldMeta(
            name="person_name",
            label="Customer Name",
            placeholder="e.g. GOUTAM MEENA",
            field_type="text",
            required=True,
            example="GOUTAM MEENA",
        ),
        TemplateFieldMeta(
            name="vehicle_number",
            label="Vehicle Number",
            placeholder="e.g. RJ14GH3252",
            field_type="text",
            required=True,
            example="RJ14GH3252",
        ),
        TemplateFieldMeta(
            name="expiry_date",
            label="Expiry Date",
            placeholder="e.g. 30-Apr-2026",
            field_type="date",
            required=True,
            example="30-Apr-2026",
        ),
        TemplateFieldMeta(
            name="authority",
            label="Issuing Authority",
            placeholder="e.g. UDAIPUR RTO MoRTH",
            field_type="text",
            required=True,
            example="UDAIPUR RTO MoRTH",
        ),
    ]

    def build_parameters(self, params: Dict[str, str]) -> List[str]:
        cleaned = self.validate_fields(params)
        # WhatsApp variable ordering: {{1}}=person_name, {{2}}=vehicle_number, {{3}}=expiry_date, {{4}}=authority
        return [
            cleaned["person_name"],
            cleaned["vehicle_number"],
            cleaned["expiry_date"],
            cleaned["authority"],
        ]

    def render_preview(self, params: Dict[str, str]) -> str:
        name = params.get("person_name", "{{1}}") or "{{1}}"
        vehicle = params.get("vehicle_number", "{{2}}") or "{{2}}"
        expiry = params.get("expiry_date", "{{3}}") or "{{3}}"
        authority = params.get("authority", "{{4}}") or "{{4}}"
        return (
            f"Kind Attention {name}\n\n"
            f"Fitness Certificate of Vehicle No. {vehicle} will expire on {expiry}.\n\n"
            "Kindly renew the certificate before the expiry date to avoid penal actions as per law.\n\n"
            f"Thanks. {authority}"
        )
