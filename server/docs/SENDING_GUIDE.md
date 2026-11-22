# Sending Your First WhatsApp Message — Step-by-Step Guide

This guide walks you through sending a WhatsApp notification using the backend API, from dry-run testing to live delivery.

---

## Prerequisites

Before sending any live messages, ensure:

1. ✅ **Meta WhatsApp Business Account** is configured.
2. ✅ **Access Token** is set in `.env` → `WHATSAPP_ACCESS_TOKEN`.
3. ✅ **Phone Number ID** (numeric) is set in `.env` → `WHATSAPP_PHONE_NUMBER_ID`.
4. ✅ **Message Templates** are submitted and approved in [WhatsApp Manager](https://business.facebook.com/wa/manage/message-templates/).
5. ✅ The FastAPI server is running (`uv run uvicorn app.main:app --reload --port 8000`).

> **Important**: `WHATSAPP_PHONE_NUMBER_ID` must be the numeric ID from Meta (e.g. `1231021533437478`), NOT the display phone number like `+1 (555) 156-0946`. Find it at **Meta Developers → WhatsApp → API Setup → Phone Number ID**.

---

## Step 1: Verify Server is Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app_env": "development",
  "dry_run_active": true,
  "whatsapp_configured": false
}
```

- `dry_run_active: true` → Messages will be **simulated** (not sent to WhatsApp).
- `whatsapp_configured: false` → Either `DRY_RUN=true` or credentials are empty.

---

## Step 2: List Available Templates

Check which templates are registered:

```bash
curl http://localhost:8000/api/templates | python3 -m json.tool
```

You will see templates like:
- `vehicle_insurance_expiry` — Requires: `vehicle_number`, `expiry_date`
- `vehicle_pucc_expiry` — Requires: `person_name`, `vehicle_number`, `expiry_date`
- `vehicle_fitness_expiry` — Requires: `person_name`, `vehicle_number`, `expiry_date`, `authority`

---

## Step 3: Preview the Message (Before Sending)

Always preview first. This does NOT send anything:

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

Verify `rendered_text` matches what you want the customer to receive.

---

## Step 4: Send Message in Dry-Run Mode (Safe Test)

With `DRY_RUN=true` in `.env`, the send endpoint simulates everything but does NOT call Meta:

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

Response:
```json
{
  "success": true,
  "message_id": "wamid.HBgL...",
  "phone_number": "+919876543210",
  "template_name": "vehicle_insurance_expiry",
  "rendered_text": "Reminder: Insurance of your vehicle RJ27GD5556 ...",
  "dry_run": true,
  "details": null
}
```

- `dry_run: true` confirms nothing was actually dispatched.
- The `message_id` is a simulated `wamid`.
- The server log shows the full Meta API payload that would have been sent.

---

## Step 5: Switch to Live Mode

When you're confident everything is correct, switch to live mode:

### 5a. Update `.env`:
```env
DRY_RUN=false
```

### 5b. Restart the server:
```bash
# Stop the running server (Ctrl+C), then restart:
uv run uvicorn app.main:app --reload --port 8000
```

### 5c. Verify health check now shows configured:
```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "app_env": "development",
  "dry_run_active": false,
  "whatsapp_configured": true
}
```

---

## Step 6: Send a Live Message

> **Warning**: This will send a real WhatsApp message and may consume your API quota / billing.

Send to your own test number first:

```bash
curl -X POST http://localhost:8000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "template_name": "vehicle_insurance_expiry",
    "parameters": {
      "vehicle_number": "RJ27GD5556",
      "expiry_date": "08-Jul-2026"
    }
  }'
```

Response on success:
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

- `dry_run: false` → The message was actually sent via Meta Cloud API.
- `message_id` → The real `wamid` returned by Meta.

---

## Phone Number Formats Accepted

The API automatically normalizes phone numbers:

| Input | Normalized |
|---|---|
| `9876543210` | `+919876543210` |
| `09876543210` | `+919876543210` |
| `+919876543210` | `+919876543210` |
| `+91 98765-43210` | `+919876543210` |
| `919876543210` | `+919876543210` |

10-digit numbers default to `+91` (India).

---

## Sending All Template Types

### Insurance Expiry
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

### PUCC Expiry
```bash
curl -X POST http://localhost:8000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "template_name": "vehicle_pucc_expiry",
    "parameters": {
      "person_name": "SHUBHAM TAMBOLI",
      "vehicle_number": "RJ14GG9920",
      "expiry_date": "23-Jun-2026"
    }
  }'
```

### Fitness Certificate Expiry
```bash
curl -X POST http://localhost:8000/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "template_name": "vehicle_fitness_expiry",
    "parameters": {
      "person_name": "GOUTAM MEENA",
      "vehicle_number": "RJ14GH3252",
      "expiry_date": "30-Apr-2026",
      "authority": "UDAIPUR RTO MoRTH"
    }
  }'
```

---

## Troubleshooting

### `422 Unprocessable Entity` — Invalid phone number
Phone number didn't pass validation. Ensure it's a 10-digit Indian mobile or a full international number.

### `400 Bad Request` — Missing required fields
Check that all template fields are included in `parameters`. Use `GET /api/templates` to see which fields are required.

### `400 Bad Request` — Unknown template
The `template_name` doesn't match any registered template. Check spelling or add it to the registry.

### `502 Bad Gateway` — Meta API failure
The Meta Cloud API returned an error or timed out. Check server logs for the exact Meta error code and message. Common causes:
- Expired or invalid access token
- Incorrect Phone Number ID
- Template not approved yet
- Recipient has not opted in / is not a valid WhatsApp user

### Message sent but not received
- Ensure the template is **approved** (not pending) in WhatsApp Manager.
- Verify the recipient's WhatsApp is active on the number you sent to.
- Check Meta's message delivery status via webhooks (future feature).
