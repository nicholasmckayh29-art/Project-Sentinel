# App Store Checklist (Phase 2)

Complete when Apple Developer account is funded by web revenue.

## Apple Developer Portal

- [ ] Enroll in Apple Developer Program ($99/yr)
- [ ] Create App ID: `com.yourorg.pricingsentinel`
- [ ] Enable Push Notifications capability
- [ ] Enable Sign in with Apple
- [ ] Create APNs key → upload to Expo/EAS

## App Store Connect

- [ ] Create app listing
- [ ] Auto-renewable subscription product (mirror Stripe $19/mo tier)
- [ ] Privacy Policy URL (host on Vercel or Supabase Storage)
- [ ] Terms of Service URL
- [ ] Screenshots (terminal aesthetic)
- [ ] App description emphasizing insider intel positioning

## RevenueCat

- [ ] Create project, link App Store Connect
- [ ] Configure entitlement `premium`
- [ ] Webhook → Supabase Edge Function (upsert `subscriptions` with `source = 'apple'`)

## Expo / EAS

- [ ] `eas.json` with development, preview, production profiles
- [ ] `eas build --platform ios --profile preview` → TestFlight
- [ ] Internal testing → public TestFlight → App Store review

## Compliance

- [ ] Privacy manifest (Expo auto-generates)
- [ ] Sign in with Apple required if offering Google/email auth
- [ ] No external payment links in iOS app (IAP only)

## Shared code ready

- Supabase schema: [`supabase/migrations/001_initial_schema.sql`](../supabase/migrations/001_initial_schema.sql)
- Design tokens: [`packages/theme/tokens.ts`](../packages/theme/tokens.ts)
- Python worker: [`backend/worker.py`](../backend/worker.py)
