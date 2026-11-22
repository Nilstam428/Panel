from abc import ABC, abstractmethod
from typing import Dict, List
from app.schemas.message import TemplateFieldMeta, TemplateInfoResponse


class BaseWhatsAppTemplate(ABC):
    """Base class for all WhatsApp approved templates."""

    name: str
    title: str
    description: str
    language_code: str = "en_US"
    fields: List[TemplateFieldMeta]

    @abstractmethod
    def build_parameters(self, params: Dict[str, str]) -> List[str]:
        """Maps named parameters from admin form to ordered WhatsApp {{1}}, {{2}}, ... parameters."""
        pass

    @abstractmethod
    def render_preview(self, params: Dict[str, str]) -> str:
        """Renders human-readable message preview for admin verification before sending."""
        pass

    def validate_fields(self, params: Dict[str, str]) -> Dict[str, str]:
        """Validates that all required fields are present and non-empty."""
        cleaned = {}
        missing = []
        for field in self.fields:
            raw_val = params.get(field.name, "")
            val = str(raw_val).strip() if raw_val is not None else ""
            if field.required and not val:
                missing.append(field.label or field.name)
            cleaned[field.name] = val

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        return cleaned

    def to_info(self) -> TemplateInfoResponse:
        """Returns API metadata description for this template."""
        sample_params = {f.name: f.example or f"[{f.name}]" for f in self.fields}
        return TemplateInfoResponse(
            name=self.name,
            title=self.title,
            description=self.description,
            language_code=self.language_code,
            fields=self.fields,
            sample_preview=self.render_preview(sample_params),
        )
