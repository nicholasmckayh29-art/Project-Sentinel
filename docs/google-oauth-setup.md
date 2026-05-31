# Google sign-in setup

Google OAuth fails when **Google Cloud**, **Supabase**, or **Vercel redirect URLs** do not match exactly.

## 1. Google Cloud Console

1. [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services → Credentials**
2. Create **OAuth client ID** → type **Web application**
3. **Authorized JavaScript origins** (add every URL users visit):
   - `http://localhost:3000`
   - `https://YOUR-APP.vercel.app`
   - Custom domain if you use one
4. **Authorized redirect URIs** — **only** the Supabase callback (not your Next.js app):

```
https://eamkkmlpphsimvznjjcf.supabase.co/auth/v1/callback
```

5. Copy **Client ID** and **Client Secret**

## 2. Supabase

1. [Authentication → Providers → Google](https://supabase.com/dashboard/project/eamkkmlpphsimvznjjcf/auth/providers)
2. Enable Google
3. Paste Client ID + Client Secret → **Save**

## 3. Supabase URL Configuration

[Authentication → URL Configuration](https://supabase.com/dashboard/project/eamkkmlpphsimvznjjcf/auth/url-configuration)

| Field | Value |
|-------|--------|
| **Site URL** | `https://YOUR-APP.vercel.app` |
| **Redirect URLs** | `http://localhost:3000/auth/callback` |
| | `https://YOUR-APP.vercel.app/auth/callback` |
| | `https://*.vercel.app/auth/callback` (preview deploys) |

## 4. Vercel env

Set **NEXT_PUBLIC_APP_URL** to your production URL (no trailing slash):

```
NEXT_PUBLIC_APP_URL=https://YOUR-APP.vercel.app
```

Redeploy after changing env vars.

## 5. Test

1. Open `/login` → **Sign in with Google**
2. After consent, you should land on `/onboarding` (or dashboard)
3. If it fails, check **Supabase → Authentication → Logs** for the error

## Common errors

| Symptom | Fix |
|---------|-----|
| `redirect_uri_mismatch` | Google redirect URI must be `…supabase.co/auth/v1/callback`, not Vercel |
| Back to login with no session | Add production `/auth/callback` to Supabase Redirect URLs; set `NEXT_PUBLIC_APP_URL` |
| `Access blocked: app not verified` | Google OAuth consent screen → add test users, or publish app |

See also [auth-email-resend.md](./auth-email-resend.md) for magic-link email to **any** user (requires verified Resend domain).
