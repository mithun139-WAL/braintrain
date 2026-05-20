# CI/CD Setup

This repository now assumes the following production split:

- `apps/web` deploys to Vercel
- `apps/api` deploys to Render

Render is the better fit for the FastAPI app because `app.main` starts an in-process APScheduler during FastAPI lifespan. That requires a long-running Python web service instead of a serverless runtime.

## What the Workflows Do

`/.github/workflows/ci.yml`

- Runs on every push and pull request
- Builds `@braintrain/shared`
- Builds the Next.js app
- Installs the FastAPI dependencies
- Compiles the Python source tree
- Smoke-imports `app.main`

`/.github/workflows/deploy-production.yml`

- Runs on pushes to `main` and on manual dispatch
- Re-runs the same validation gates
- Deploys the exact `GITHUB_SHA` to Render
- Waits for the Render deploy to reach a live state
- Deploys the web app to Vercel
- Smoke-checks the API health endpoint and the Vercel deployment URL

The current CI gate is build and startup smoke checks. This repo is mid-migration, so frontend linting and backend Ruff enforcement are not wired in as blocking checks yet.

## Vercel Setup

1. Create a Vercel project from this GitHub repository.
2. Set the project Root Directory to `apps/web`.
3. Add the production environment variable:

```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

4. If GitHub Actions is your source of truth for production deploys, disable automatic production deployments in Vercel.
5. From the repo root, run `vercel link` once and record the generated `orgId` and `projectId` from `.vercel/project.json`.

## Render Setup

Create a Render Web Service for `apps/api` with these settings:

- Root Directory: `apps/api`
- Runtime: `Python`
- Build Command: `uv sync --frozen`
- Pre-Deploy Command: `uv run alembic upgrade head`
- Start Command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Recommended:

- Disable Render auto-deploys if GitHub Actions will trigger production deploys
- Keep at least one always-on instance because the scheduler runs inside the API service

## Stripe Production Setup

Stripe billing is handled by FastAPI, not by the Next.js app.

Production Stripe traffic must point to the Render API URL:

```text
POST https://api.your-domain.com/billing/webhook
```

Create a live Stripe product and recurring price, then add these Render environment variables:

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_SUCCESS_URL=https://your-web-domain.com/dashboard/settings?billing=success
STRIPE_CANCEL_URL=https://your-web-domain.com/dashboard/settings?billing=cancelled
STRIPE_PORTAL_RETURN_URL=https://your-web-domain.com/dashboard/settings
```

Subscribe the Stripe live webhook to these events:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `customer.subscription.paused`

Also set:

```env
FRONTEND_URL=https://your-web-domain.com
```

## Other Required Render Environment Variables

At minimum, also configure:

```env
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=...
```

Then add any other real production values your app needs, such as:

- `GOOGLE_CLIENT_ID`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- `OPENAI_API_KEY`, `NVIDIA_API_KEY`, `GROQ_API_KEY`

## GitHub Secrets and Variables

Add these GitHub Actions secrets:

```text
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
RENDER_API_KEY
RENDER_SERVICE_ID
```

Add this GitHub Actions variable:

```text
API_HEALTHCHECK_URL=https://api.your-domain.com/
```

Use the `production` environment in GitHub if you want approval gates and environment-scoped secrets.

## First Production Rollout Checklist

1. Configure Vercel and Render manually once.
2. Add all production env vars in Vercel and Render.
3. Add the GitHub secrets and `API_HEALTHCHECK_URL` variable.
4. Push to `main`.
5. Confirm the Render deploy reaches `live`.
6. Confirm the Vercel deployment URL loads.
7. Complete one real Stripe checkout in live mode and confirm the webhook updates the user to `PRO`.
