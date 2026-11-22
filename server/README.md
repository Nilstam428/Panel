# WhatsApp Admin Notification Bot — Backend

FastAPI backend service for manually triggering compliance and expiry notification messages (Insurance, PUCC, Fitness) via **Meta WhatsApp Cloud API**.

Based on official Meta Cloud API specifications (reference: [Jasper's Market Sample](https://github.com/fbsamples/whatsapp-business-jaspers-market)) and the project roadmap in [to_do.md](file:///home/nilesh/Data/Client/server/to_do.md).

---

## Architecture Flow

```text
Admin UI / REST API
         │
         ▼
 FastAPI Backend (port 8000)
         │
         ├── 1. Phone number normalization (+91 E.164)
         ├── 2. Template validation & variable mapping
         ├── 3. Render preview for admin verification
         │
         ▼
 WhatsApp Service (httpx)
         │
  [DRY_RUN=true] ───────────────► Local Simulator (Generates mock wamid...)
         │
  [DRY_RUN=false] ──────────────► Meta Graph API (https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages)
                                         │
                                         ▼
                                  Customer WhatsApp
```

---

## Features

- **Standardized WhatsApp Templates**:
  - **Vehicle Insurance Expiry** (`vehicle_insurance_expiry`)
  - **Vehicle PUCC Expiry** (`vehicle_pucc_expiry`)
  - **Vehicle Fitness Expiry** (`vehicle_fitness_expiry`)
- **Extensible Template Registry**: Add new templates easily by subclassing `BaseWhatsAppTemplate`.
- **Preview Before Send**: Admins can verify rendered message text and variable bindings before dispatching.
- **Dry-Run / Mock Mode (`DRY_RUN=true`)**: Test full API payloads and responses locally without live Meta credentials or incurring billing charges.
- **Phone Number Normalization**: Automatically converts 10-digit Indian numbers (`9876543210`) into international E.164 format (`+919876543210`).
- **Interactive API Documentation**: Built-in Swagger UI at `/docs` and ReDoc at `/redoc`.
- **Automated Tests**: Comprehensive test suite using `pytest` and `pytest-asyncio`.

---

## Project Structure

```text
server/
├── .env                  # Local environment configuration (do not commit secrets)
├── .env.example          # Environment variable template
├── .gitignore            # Git exclusion rules
├── pyproject.toml        # Dependencies managed by uv
├── to_do.md              # Project roadmap & milestones
├── app/
│   ├── main.py           # FastAPI entry point & CORS configuration
│   ├── config.py         # Application settings loaded via pydantic-settings
│   ├── api/
│   │   └── message_routes.py  # REST endpoints for templates and sending
│   ├── schemas/
│   │   ├── message.py    # Admin request/response and phone normalization schemas
│   │   └── whatsapp.py   # Meta Cloud API typed payload schemas
│   ├── services/
│   │   ├── template_service.py # Template validation & parameter builder
│   │   └── whatsapp_service.py # Meta Cloud API client + Dry-Run simulator
│   └── templates/
│       ├── base.py       # Abstract base template class
│       ├── registry.py   # Central template registry
│       ├── insurance.py  # Insurance expiry template
│       ├── pucc.py       # PUCC expiry template
│       └── fitness.py    # Fitness certificate expiry template
└── tests/
    ├── test_api.py       # FastAPI integration and endpoint tests
    └── test_templates.py # Unit tests for phone normalization & template rendering
```

---

## Getting Started

### 1. Prerequisites

- Python 3.11 or higher
- [`uv`](https://docs.astral.sh/uv/) package and environment manager

### 2. Virtual Environment Setup

The virtual environment is created using `uv`:

```bash
# Create virtual environment
uv venv .venv

# Activate environment
source .venv/bin/activate
```

Dependencies can be installed or updated via `uv add`:

```bash
uv add fastapi "uvicorn[standard]" httpx pydantic pydantic-settings
uv add --dev pytest pytest-asyncio
```

### 3. Environment Configuration (`.env`)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Meta WhatsApp Cloud API Configuration
WHATSAPP_API_BASE_URL=https://graph.facebook.com
WHATSAPP_API_VERSION=v20.0
WHATSAPP_ACCESS_TOKEN="your_meta_access_token"
WHATSAPP_PHONE_NUMBER_ID="your_numeric_phone_number_id"
WHATSAPP_WABA_ID="your_waba_id"

# Application Settings
APP_ENV=development
DRY_RUN=true
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=["*"]
```

> [!IMPORTANT]
> **Phone Number ID vs Display Number**:
> In Meta WhatsApp Cloud API, `WHATSAPP_PHONE_NUMBER_ID` must be the **numeric ID** (e.g. `104829104928374`), **NOT** the phone number string like `+1 (555) 156-0946`.
> You can find this numeric ID on your [Meta Developers Portal](https://developers.facebook.com/) under **WhatsApp > API Setup > Phone Number ID**.

> [!TIP]
> **Testing Without Live Credentials**:
> Leave `DRY_RUN=true` to test the API immediately. In dry-run mode, the server simulates sending, returns a simulated `wamid...`, and logs the full payload that would be sent to Meta.

---

## Running the Server

Start the FastAPI development server:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- **API Base URL**: `http://localhost:8000`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## API Endpoints

### 1. Health Check
`GET /health`

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "app_env": "development",
  "dry_run_active": true,
  "whatsapp_configured": false
}
```

---

### 2. List Available Templates
`GET /api/templates`

Returns all registered templates, including field metadata, labels, and preview samples.

```bash
curl http://localhost:8000/api/templates
```

---

### 3. Preview Message
`POST /api/messages/preview`

Render the message text using variable inputs prior to sending.

```bash
curl -X POST http://localhost:8000/api/messages/preview \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "vehicle_insurance_expiry",
    "parameters": {
      "vehicle_number": "RJ27GD5556",
      "expiry_date": "08-Jul-2026"
    }
  }'
```

Response:
```json
{
  "template_name": "vehicle_insurance_expiry",
  "rendered_text": "Reminder: Insurance of your vehicle RJ27GD5556 expires on 08-Jul-2026. Please renew before due date to comply with Section 146 of MV Act, 1988. MoRTH",
  "parameters": ["RJ27GD5556", "08-Jul-2026"]
}
```

---

### 4. Send WhatsApp Notification
`POST /api/messages/send`

Validates recipient and variables, constructs the Meta Cloud API payload, and dispatches the message.

#### Example 1: Vehicle Insurance Expiry
```bash
curl -X POST http://localhost:8000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "template_name": "vehicle_insurance_expiry",
    "parameters": {
      "vehicle_number": "RJ27GD5556",
      "expiry_date": "08-Jul-2026"
    }
  }'
```

#### Example 2: PUCC Expiry
```bash
curl -X POST http://localhost:8000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "template_name": "vehicle_pucc_expiry",
    "parameters": {
      "person_name": "SHUBHAM TAMBOLI",
      "vehicle_number": "RJ14GG9920",
      "expiry_date": "23-Jun-2026"
    }
  }'
```

#### Example 3: Fitness Certificate Expiry
```bash
curl -X POST http://localhost:8000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "template_name": "vehicle_fitness_expiry",
    "parameters": {
      "person_name": "GOUTAM MEENA",
      "vehicle_number": "RJ14GH3252",
      "expiry_date": "30-Apr-2026",
      "authority": "UDAIPUR RTO MoRTH"
    }
  }'
```

Response:
```json
{
  "success": true,
  "message_id": "wamid.HBgL...",
  "phone_number": "+919876543210",
  "template_name": "vehicle_insurance_expiry",
  "rendered_text": "Reminder: Insurance of your vehicle RJ27GD5556 expires on 08-Jul-2026...",
  "dry_run": true,
  "details": null
}
```

---

## Running Tests

Run the automated test suite using `pytest`:

```bash
uv run pytest tests/ -v
```

Output:
```text
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_list_templates PASSED
tests/test_api.py::test_preview_message PASSED
tests/test_api.py::test_send_message_dry_run PASSED
tests/test_api.py::test_send_message_invalid_phone PASSED
tests/test_api.py::test_send_message_missing_parameter PASSED
tests/test_templates.py::test_normalize_phone_number PASSED
tests/test_templates.py::test_template_registry PASSED
tests/test_templates.py::test_insurance_template PASSED
tests/test_templates.py::test_pucc_template PASSED
tests/test_templates.py::test_fitness_template PASSED
tests/test_templates.py::test_missing_fields PASSED
============================== 12 passed in 0.51s ==============================
```

---

## How to Add New Templates

1. Create a new file under `app/templates/` (e.g. `driving_license.py`):
   ```python
   from app.templates.base import BaseWhatsAppTemplate
   from app.schemas.message import TemplateFieldMeta

   class DrivingLicenseExpiryTemplate(BaseWhatsAppTemplate):
       name = "driving_license_expiry"
       title = "Driving License Expiry"
       description = "Notifies customer of license renewal due date."
       fields = [
           TemplateFieldMeta(name="holder_name", label="License Holder Name", required=True),
           TemplateFieldMeta(name="license_number", label="DL Number", required=True),
           TemplateFieldMeta(name="expiry_date", label="Expiry Date", required=True),
       ]

       def build_parameters(self, params):
           cleaned = self.validate_fields(params)
           return [cleaned["holder_name"], cleaned["license_number"], cleaned["expiry_date"]]

       def render_preview(self, params):
           return f"Dear {params.get('holder_name')}, your DL {params.get('license_number')} expires on {params.get('expiry_date')}."
   ```

2. Register it in `app/templates/registry.py`:
   ```python
   self.register(DrivingLicenseExpiryTemplate())
   ```

It will automatically become available in `GET /api/templates`, `POST /api/messages/preview`, and `POST /api/messages/send`.
