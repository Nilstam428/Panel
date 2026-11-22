# FastAPI + Vite frontend

The React/Vite dashboard now lives in `server/frontend` alongside the FastAPI project. This directory is a standard Vite app and can be deployed independently as a Vercel static site.

## Vercel

Set the Vercel project's **Root Directory** to `server/frontend`. Vercel will use `vercel.json` to install dependencies, run `npm run build`, and publish `dist`.

Set `VITE_API_BASE_URL` in the Vercel project environment to the public base URL of the FastAPI deployment (for example, `https://your-api.example.com`). Leave it unset only when the API is served from the same origin. The API must allow the deployed frontend origin in its CORS settings.

## Local development

```bash
cd server/frontend
npm install
npm run dev
```

Configure `VITE_API_BASE_URL` in a `.env.local` file if the FastAPI API is not available at the same origin. The app expects the API routes `/api/templates`, `/api/messages/preview`, and `/api/messages/send`.
