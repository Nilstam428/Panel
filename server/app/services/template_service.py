from typing import Dict, List, Tuple
from app.schemas.message import TemplateInfoResponse
from app.schemas.whatsapp import (
    WhatsAppBodyComponent,
    WhatsAppLanguage,
    WhatsAppTemplatePayload,
    WhatsAppTextParameter,
)
from app.templates.registry import TemplateRegistry, get_template_registry


class TemplateService:
    def __init__(self, registry: TemplateRegistry = None):
        self.registry = registry or get_template_registry()

    def get_available_templates(self) -> List[TemplateInfoResponse]:
        """Returns all registered templates with their metadata."""
        return [t.to_info() for t in self.registry.list_all()]

    def preview_template(
        self, template_name: str, params: Dict[str, str]
    ) -> Tuple[str, List[str]]:
        """Renders preview text and ordered parameters for a given template."""
        template = self.registry.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: '{template_name}'")

        # Check required fields
        template.validate_fields(params)
        rendered_text = template.render_preview(params)
        ordered_params = template.build_parameters(params)
        return rendered_text, ordered_params

    def build_meta_payload(
        self, template_name: str, params: Dict[str, str]
    ) -> Tuple[WhatsAppTemplatePayload, str]:
        """Builds Meta Cloud API WhatsAppTemplatePayload structure and rendered text preview."""
        rendered_text, ordered_params = self.preview_template(template_name, params)
        template = self.registry.get(template_name)

        meta_components = [
            WhatsAppBodyComponent(
                type="body",
                parameters=[
                    WhatsAppTextParameter(type="text", text=param_text)
                    for param_text in ordered_params
                ],
            )
        ]

        payload = WhatsAppTemplatePayload(
            name=template.name,
            language=WhatsAppLanguage(code=template.language_code),
            components=meta_components,
        )

        return payload, rendered_text
