import pytest
from app.schemas.message import normalize_phone_number
from app.templates.registry import get_template_registry


def test_normalize_phone_number():
    # 10-digit Indian phone
    assert normalize_phone_number("9876543210") == "+919876543210"
    # With leading +91
    assert normalize_phone_number("+919876543210") == "+919876543210"
    # With spaces or hyphens
    assert normalize_phone_number("+91 98765-43210") == "+919876543210"
    # With leading 0
    assert normalize_phone_number("09876543210") == "+919876543210"

    # Invalid length
    with pytest.raises(ValueError):
        normalize_phone_number("12345")


def test_template_registry():
    registry = get_template_registry()
    templates = registry.list_all()
    assert len(templates) >= 3

    assert registry.exists("vehicle_insurance_expiry")
    assert registry.exists("vehicle_pucc_expiry")
    assert registry.exists("vehicle_fitness_expiry")


def test_insurance_template():
    registry = get_template_registry()
    tmpl = registry.get("vehicle_insurance_expiry")
    assert tmpl is not None

    params = {
        "vehicle_number": "RJ27GD5556",
        "expiry_date": "08-Jul-2026",
    }
    ordered = tmpl.build_parameters(params)
    assert ordered == ["RJ27GD5556", "08-Jul-2026"]

    preview = tmpl.render_preview(params)
    assert "RJ27GD5556" in preview
    assert "08-Jul-2026" in preview
    assert "Section 146 of MV Act" in preview


def test_pucc_template():
    registry = get_template_registry()
    tmpl = registry.get("vehicle_pucc_expiry")
    assert tmpl is not None

    params = {
        "person_name": "SHUBHAM TAMBOLI",
        "vehicle_number": "RJ14GG9920",
        "expiry_date": "23-Jun-2026",
    }
    ordered = tmpl.build_parameters(params)
    assert ordered == ["SHUBHAM TAMBOLI", "RJ14GG9920", "23-Jun-2026"]

    preview = tmpl.render_preview(params)
    assert "SHUBHAM TAMBOLI" in preview
    assert "RJ14GG9920" in preview
    assert "23-Jun-2026" in preview


def test_fitness_template():
    registry = get_template_registry()
    tmpl = registry.get("vehicle_fitness_expiry")
    assert tmpl is not None

    params = {
        "person_name": "GOUTAM MEENA",
        "vehicle_number": "RJ14GH3252",
        "expiry_date": "30-Apr-2026",
        "authority": "UDAIPUR RTO MoRTH",
    }
    ordered = tmpl.build_parameters(params)
    assert ordered == [
        "GOUTAM MEENA",
        "RJ14GH3252",
        "30-Apr-2026",
        "UDAIPUR RTO MoRTH",
    ]

    preview = tmpl.render_preview(params)
    assert "GOUTAM MEENA" in preview
    assert "RJ14GH3252" in preview
    assert "30-Apr-2026" in preview
    assert "UDAIPUR RTO MoRTH" in preview


def test_missing_fields():
    registry = get_template_registry()
    tmpl = registry.get("vehicle_insurance_expiry")
    with pytest.raises(ValueError, match="Missing required fields"):
        tmpl.build_parameters({"vehicle_number": "RJ27GD5556"})
