from typing import Dict, List, Optional
from app.templates.base import BaseWhatsAppTemplate
from app.templates.insurance import VehicleInsuranceExpiryTemplate
from app.templates.pucc import VehiclePUCCExpiryTemplate
from app.templates.fitness import VehicleFitnessExpiryTemplate


class TemplateRegistry:
    """Central registry for WhatsApp message templates."""

    def __init__(self):
        self._templates: Dict[str, BaseWhatsAppTemplate] = {}
        # Register default templates
        self.register(VehicleInsuranceExpiryTemplate())
        self.register(VehiclePUCCExpiryTemplate())
        self.register(VehicleFitnessExpiryTemplate())

    def register(self, template: BaseWhatsAppTemplate) -> None:
        """Register a new template."""
        self._templates[template.name] = template

    def get(self, name: str) -> Optional[BaseWhatsAppTemplate]:
        """Fetch template by exact name."""
        return self._templates.get(name)

    def list_all(self) -> List[BaseWhatsAppTemplate]:
        """Return all registered templates."""
        return list(self._templates.values())

    def exists(self, name: str) -> bool:
        """Check if a template name is registered."""
        return name in self._templates


# Global singleton registry
registry = TemplateRegistry()


def get_template_registry() -> TemplateRegistry:
    return registry
