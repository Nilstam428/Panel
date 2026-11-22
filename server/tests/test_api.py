import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "dry_run_active" in data


@pytest.mark.asyncio
async def test_list_templates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/templates")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) >= 3
    names = [t["name"] for t in templates]
    assert "vehicle_insurance_expiry" in names
    assert "vehicle_pucc_expiry" in names
    assert "vehicle_fitness_expiry" in names


@pytest.mark.asyncio
async def test_preview_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/messages/preview",
            json={
                "template_name": "vehicle_insurance_expiry",
                "parameters": {
                    "vehicle_number": "RJ27GD5556",
                    "expiry_date": "08-Jul-2026",
                },
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "RJ27GD5556" in data["rendered_text"]
    assert data["parameters"] == ["RJ27GD5556", "08-Jul-2026"]


@pytest.mark.asyncio
async def test_send_message_dry_run():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/messages/send",
            json={
                "phone_number": "9876543210",
                "template_name": "vehicle_insurance_expiry",
                "parameters": {
                    "vehicle_number": "RJ27GD5556",
                    "expiry_date": "08-Jul-2026",
                },
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["phone_number"] == "+919876543210"
    assert data["message_id"].startswith("wamid.")
    assert data["dry_run"] is True


@pytest.mark.asyncio
async def test_send_message_invalid_phone():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/messages/send",
            json={
                "phone_number": "123",
                "template_name": "vehicle_insurance_expiry",
                "parameters": {
                    "vehicle_number": "RJ27GD5556",
                    "expiry_date": "08-Jul-2026",
                },
            },
        )
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_send_message_missing_parameter():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/messages/send",
            json={
                "phone_number": "9876543210",
                "template_name": "vehicle_insurance_expiry",
                "parameters": {
                    "vehicle_number": "RJ27GD5556"
                    # missing expiry_date
                },
            },
        )
    assert response.status_code == 400
    assert "Missing required fields" in response.json()["detail"]
