# FastAPI + Vite frontend

The React/Vite dashboard lives in `server/frontend`; the FastAPI app is in `server/app`. The repository-root `vercel.json` builds and routes both as one Vercel deployment. Requests to `/api/*` go to FastAPI, and all other paths serve the Vite SPA from the same origin.

## Vercel setup

1. Import this repository into Vercel and set **Root Directory** to the repository root (`.`), not `server` or `server/frontend`.
2. Let the root `vercel.json` provide the build and routing configuration.
3. Set the WhatsApp credentials and other backend settings (`DRY_RUN`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, etc.) as Vercel environment variables. Keep `DRY_RUN=true` until live sending is intentionally configured.
4. No `VITE_API_BASE_URL` is needed for this unified deployment: the frontend calls `/api/...` on its own origin. Do not configure this Vercel project to deploy only `server/frontend`.

The API routes remain `/api/templates`, `/api/messages/preview`, and `/api/messages/send`. Because the browser and API share an origin, this setup avoids cross-origin requests and their CORS configuration requirements.

## Local frontend development

```bash
cd server/frontend
npm install
npm run dev
```

When running the Vite development server separately from FastAPI, set `VITE_API_BASE_URL` to the FastAPI server URL in `server/frontend/.env.local`; for example, `http://localhost:8000`. Configure FastAPI CORS to allow the Vite dev-server origin when using this split local setup.
