# MAYDON — Namangan sports discovery MVP

One repository: Telegram bot (`bot/`), FastAPI backend (`backend/`), React + TypeScript Mini App (`miniapp/`). Sports: football, table tennis, billiards. The UI is inspired by the supplied Home/Profile screenshot, not a pixel-perfect Figma export.

## Run locally

1. Install Python 3.12+ and Node.js 20+.
2. Copy `.env.example` to `.env` and fill in private values. **Never share BOT_TOKEN or commit .env.**
3. Backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload` (default http://localhost:8000). To persist DB locally, set `DATABASE_PATH=./maydon.db` in your shell before starting.
4. Frontend: `cd miniapp && npm install`; create `miniapp/.env.local` containing `VITE_API_URL=http://localhost:8000` and `VITE_YANDEX_MAPS_KEY=...`; run `npm run dev`.
5. Bot: `cd bot && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python main.py` from a shell with BOT_TOKEN and MINI_APP_URL exported, or copy .env into bot folder for local testing.
6. Telegram requires a **public HTTPS URL** for the Mini App; localhost works only in a normal browser. Host frontend and backend separately and set correct URLs. Set BotFather menu button or use `/start`.

## API routes

- `GET /venues` — approved venues only.
- `POST /venues` — owner registration, pending approval.
- `GET /admin/venues` and `POST /admin/venues/{id}/approved|rejected` — approval flow.
- `POST /bookings` — booking request.
- `GET /owner/bookings` and `POST /owner/bookings/{id}/confirmed|rejected` — owner workflow.

## IMPORTANT before public deployment

This is a **development scaffold**, not production-ready. Owner/admin API currently trusts `x-telegram-user-id` headers, and booking creation trusts submitted user IDs. **Do not expose write endpoints publicly until server-side Telegram Mini App `initData` HMAC verification, session/role checks, rate limits, booking conflict prevention, and owner notifications are implemented.** Do not use the placeholder demo venue as a real listing. Yandex Maps JavaScript API key is visible to browsers; apply allowed-domain restrictions and check Yandex API terms/pricing. No live Yandex Places search is included; map pins are from your approved database. Booking requests are recorded but do not yet notify owners. All listings must be verified before publication.
# maydon-bot
