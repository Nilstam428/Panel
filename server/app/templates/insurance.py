from typing import Dict, List
from app.schemas.message import TemplateFieldMeta
from app.templates.base import BaseWhatsAppTemplate


class VehicleInsuranceExpiryTemplate(BaseWhatsAppTemplate):
    name = "vehicle_insurance_expiry"
    title = "Vehicle Insurance Expiry"
    description = "Notifies customer regarding upcoming vehicle insurance expiration under Section 146 MV Act."
    language_code = "en_US"

    fields = [
        TemplateFieldMeta(
            name="vehicle_number",
            label="Vehicle Number",
            placeholder="e.g. RJ27GD5556",
            field_type="text",
            required=True,
            example="RJ27GD5556",
        ),
        TemplateFieldMeta(
            name="expiry_date",
            label="Expiry Date",
            placeholder="e.g. 08-Jul-2026",
            field_type="date",
            required=True,
            example="08-Jul-2026",
        ),
    ]

    def build_parameters(self, params: Dict[str, str]) -> List[str]:
        cleaned = self.validate_fields(params)
        # WhatsApp variable ordering: {{1}}=vehicle_number, {{2}}=expiry_date
        return [
            cleaned["vehicle_number"],
            cleaned["expiry_date"],
        ]

    def render_preview(self, params: Dict[str, str]) -> str:
        vehicle = params.get("vehicle_number", "{{1}}") or "{{1}}"
        expiry = params.get("expiry_date", "{{2}}") or "{{2}}"
        return (
            f"Reminder: Insurance of your vehicle {vehicle} expires on {expiry}. "
            "Please renew before due date to comply with Section 146 of MV Act, 1988. MoRTH"
        )
