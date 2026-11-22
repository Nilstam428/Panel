# API Integration Guide — WhatsApp Admin Notification Bot

Complete reference for integrating with the FastAPI backend from any frontend (Next.js, React, mobile app, or scripts).

---

## Base Configuration

| Setting | Value |
|---|---|
| **Base URL** | `http://localhost:8000` (development) |
| **Content-Type** | `application/json` |
| **Authentication** | None yet (Phase 8 in roadmap) |

---

## Endpoint Reference

### `GET /health`

Check if the backend is running and how it's configured.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "app_env": "development",
  "dry_run_active": true,
  "whatsapp_configured": false
}
```

| Field | Type | Description |
|---|---|---|
| `status` | `string` | Always `"healthy"` if the server is running |
| `app_env` | `string` | `"development"` or `"production"` |
| `dry_run_active` | `boolean` | `true` = messages are simulated, not sent to Meta |
| `whatsapp_configured` | `boolean` | `true` = credentials present AND `DRY_RUN=false` |

---

### `GET /api/templates`

Fetch all registered message templates. Use this to dynamically build the admin form.

**Response** `200 OK`:
```json
[
  {
    "name": "vehicle_insurance_expiry",
    "title": "Vehicle Insurance Expiry",
    "description": "Notifies customer regarding upcoming vehicle insurance expiration under Section 146 MV Act.",
    "language_code": "en_US",
    "fields": [
      {
        "name": "vehicle_number",
        "label": "Vehicle Number",
        "placeholder": "e.g. RJ27GD5556",
        "field_type": "text",
        "required": true,
        "example": "RJ27GD5556"
      },
      {
        "name": "expiry_date",
        "label": "Expiry Date",
        "placeholder": "e.g. 08-Jul-2026",
        "field_type": "date",
        "required": true,
        "example": "08-Jul-2026"
      }
    ],
    "sample_preview": "Reminder: Insurance of your vehicle RJ27GD5556 expires on 08-Jul-2026. ..."
  }
]
```

#### Template Fields Schema

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Field key to use in `parameters` |
| `label` | `string` | Human-readable label for form display |
| `placeholder` | `string` | Example value for input placeholder |
| `field_type` | `string` | `"text"` or `"date"` — hint for input type |
| `required` | `boolean` | Whether the field is mandatory |
| `example` | `string` | Sample value |

**Frontend usage**: Loop over `fields` to dynamically render form inputs for the selected template.

---

### `POST /api/messages/preview`

Renders the final message text using provided variables. Does NOT send anything. Use this for the **Preview** step in the admin workflow.

**Request Body**:
```json
{
  "template_name": "vehicle_insurance_expiry",
  "parameters": {
    "vehicle_number": "RJ27GD5556",
    "expiry_date": "08-Jul-2026"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `template_name` | `string` | ✅ | Exact template `name` from `GET /api/templates` |
| `parameters` | `object` | ✅ | Key-value pairs matching the template's `fields[].name` |

**Response** `200 OK`:
```json
{
  "template_name": "vehicle_insurance_expiry",
  "rendered_text": "Reminder: Insurance of your vehicle RJ27GD5556 expires on 08-Jul-2026. Please renew before due date to comply with Section 146 of MV Act, 1988. MoRTH",
  "parameters": ["RJ27GD5556", "08-Jul-2026"]
}
```

| Field | Type | Description |
|---|---|---|
| `rendered_text` | `string` | The full message exactly as the customer will see it |
| `parameters` | `string[]` | Ordered WhatsApp variables (`{{1}}`, `{{2}}`, ...) |

**Error** `400`:
```json
{
  "detail": "Missing required fields: Expiry Date"
}
```

---

### `POST /api/messages/send`

Validates, builds Meta Cloud API payload, and dispatches the WhatsApp message (or simulates in dry-run mode).

**Request Body**:
```json
{
  "phone_number": "9876543210",
  "template_name": "vehicle_insurance_expiry",
  "parameters": {
    "vehicle_number": "RJ27GD5556",
    "expiry_date": "08-Jul-2026"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | `string` | ✅ | Recipient number. Auto-normalizes (see below) |
| `template_name` | `string` | ✅ | Template name from `GET /api/templates` |
| `parameters` | `object` | ✅ | Key-value pairs for template variables |

**Phone number normalization** (handled server-side):

| Input | Normalized Result |
|---|---|
| `9876543210` | `+919876543210` |
| `09876543210` | `+919876543210` |
| `+919876543210` | `+919876543210` |
| `+91 98765 43210` | `+919876543210` |

**Response** `200 OK`:
```json
{
  "success": true,
  "message_id": "wamid.HBgLOTE5ODc2NTQzMjEw...",
  "phone_number": "+919876543210",
  "template_name": "vehicle_insurance_expiry",
  "rendered_text": "Reminder: Insurance of your vehicle RJ27GD5556 ...",
  "dry_run": false,
  "details": null
}
```

| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | `true` on successful dispatch |
| `message_id` | `string` | WhatsApp message ID (`wamid.xxx`). Simulated if `dry_run` |
| `phone_number` | `string` | Normalized E.164 format |
| `rendered_text` | `string` | The rendered message text |
| `dry_run` | `boolean` | `true` = simulated, `false` = sent to Meta Cloud API |
| `details` | `object\|null` | Reserved for future metadata |

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Cause | Example `detail` |
|---|---|---|
| `400` | Missing fields, unknown template, Meta API rejection | `"Missing required fields: Expiry Date"` |
| `422` | Invalid input (e.g. bad phone number format) | Pydantic validation error |
| `502` | Meta Cloud API timeout or connection failure | `"Failed to send WhatsApp message via Meta Cloud API."` |

---

## Frontend Integration Examples

### JavaScript / Fetch API

```javascript
const API_BASE = "http://localhost:8000";

// 1. Fetch templates
async function getTemplates() {
  const res = await fetch(`${API_BASE}/api/templates`);
  return res.json();
}

// 2. Preview message
async function previewMessage(templateName, parameters) {
  const res = await fetch(`${API_BASE}/api/messages/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      template_name: templateName,
      parameters: parameters,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail);
  }
  return res.json();
}

// 3. Send message
async function sendMessage(phoneNumber, templateName, parameters) {
  const res = await fetch(`${API_BASE}/api/messages/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      phone_number: phoneNumber,
      template_name: templateName,
      parameters: parameters,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail);
  }
  return res.json();
}
```

### React Hook Example

```jsx
import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

function useTemplates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/templates`)
      .then((res) => res.json())
      .then(setTemplates)
      .finally(() => setLoading(false));
  }, []);

  return { templates, loading };
}

function useSendMessage() {
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function send(phoneNumber, templateName, parameters) {
    setSending(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/messages/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone_number: phoneNumber,
          template_name: templateName,
          parameters: parameters,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Send failed");
      }

      const data = await res.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setSending(false);
    }
  }

  return { send, sending, result, error };
}
```

### Python / httpx Example

```python
import httpx

API_BASE = "http://localhost:8000"

async def send_insurance_reminder():
    async with httpx.AsyncClient() as client:
        # Preview first
        preview = await client.post(
            f"{API_BASE}/api/messages/preview",
            json={
                "template_name": "vehicle_insurance_expiry",
                "parameters": {
                    "vehicle_number": "RJ27GD5556",
                    "expiry_date": "08-Jul-2026",
                },
            },
        )
        print("Preview:", preview.json()["rendered_text"])

        # Send
        result = await client.post(
            f"{API_BASE}/api/messages/send",
            json={
                "phone_number": "+919876543210",
                "template_name": "vehicle_insurance_expiry",
                "parameters": {
                    "vehicle_number": "RJ27GD5556",
                    "expiry_date": "08-Jul-2026",
                },
            },
        )
        data = result.json()
        print(f"Sent: {data['success']}, ID: {data['message_id']}, Dry-run: {data['dry_run']}")
```

---

## Recommended Admin Panel Workflow

The frontend should follow this sequence for every message:

```
1. GET /api/templates
   ↓
   Admin selects a template
   ↓
2. Dynamic form renders based on template fields
   ↓
   Admin fills in: phone number + template variables
   ↓
3. POST /api/messages/preview
   ↓
   Admin verifies rendered message text
   ↓
4. Admin clicks "Send WhatsApp"
   ↓
5. POST /api/messages/send
   ↓
   Show success (message_id) or error
```

Important frontend rules:
- **Disable the Send button** while the request is in progress (prevent double-sends).
- **Always preview first** — do not allow sending without admin verification.
- **Never construct the WhatsApp message on the frontend** — the backend handles all template rendering.
- **Show `dry_run` status** clearly in the UI so the admin knows if it was real or simulated.

---

## Meta WhatsApp Cloud API Payload Reference

When the backend sends a live message, it constructs this exact JSON for Meta's Graph API:

```
POST https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json
```

```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "919876543210",
  "type": "template",
  "template": {
    "name": "vehicle_insurance_expiry",
    "language": {
      "code": "en_US"
    },
    "components": [
      {
        "type": "body",
        "parameters": [
          { "type": "text", "text": "RJ27GD5556" },
          { "type": "text", "text": "08-Jul-2026" }
        ]
      }
    ]
  }
}
```

Meta's success response:
```json
{
  "messaging_product": "whatsapp",
  "contacts": [
    { "input": "919876543210", "wa_id": "919876543210" }
  ],
  "messages": [
    { "id": "wamid.HBgLOTE5ODc2NTQzMjEwFQIAERgSM0ZCQTM0..." }
  ]
}
```

Reference: [Meta WhatsApp Cloud API — Send Template Message](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates)

---

## Interactive API Docs

The FastAPI server provides auto-generated interactive documentation:

| Tool | URL |
|---|---|
| **Swagger UI** (try-it-out) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **ReDoc** (read-only reference) | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| **OpenAPI JSON** | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) |

You can test all endpoints directly from Swagger UI without any external tools.
