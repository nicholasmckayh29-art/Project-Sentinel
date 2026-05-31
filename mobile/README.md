# iOS App — Phase 2 (Post-Revenue)

The web app ships first on Vercel + Supabase. When web subscriptions fund the Apple Developer account ($99/yr), scaffold the native app here.

## Planned stack

- **Expo** (React Native) — TestFlight via EAS Build
- **RevenueCat** — Apple IAP (same `subscriptions` table, `source = 'apple'`)
- **Shared theme** — import from [`packages/theme/`](../packages/theme/tokens.ts)

## Pre-built backend (ready now)

| Feature | Status |
|---------|--------|
| Supabase Auth | Ready — add Sign in with Apple |
| Watchlists | Ready — same tables |
| Alerts feed | Ready — Realtime on `alerts` |
| Subscriptions | Ready — add RevenueCat webhook alongside Stripe |
| Push tokens | Add `push_tokens` table + Expo Push fan-out in worker |

## Checklist when funded

See [`docs/app-store-checklist.md`](../docs/app-store-checklist.md)

## Do not build until

- [ ] Web app live on Vercel
- [ ] Stripe subscriptions working
- [ ] Apple Developer account active
