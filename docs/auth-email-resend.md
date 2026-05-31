# Fix Auth Email Rate Limits (Resend SMTP)

Supabase's built-in mailer allows ~**4 emails/hour**. This guide switches magic-link login to **Resend** (100/day free).

## Step 1 — Resend account

1. Go to [resend.com](https://resend.com) → Sign up (free)
2. **API Keys** → Create API Key → copy `re_...`

### Sender address (pick one)

**A) Quick test (no domain)** — only sends to **your** Resend signup email:

- Use sender: `onboarding@resend.dev`
- **Other users will NOT receive magic links** until you complete option B

**B) Production (required for other users)** — send to any user:

1. Resend → **Domains** → Add domain
2. Add the DNS records Resend shows (TXT, MX, etc.)
3. Wait for verification
4. Use sender like `intel@yourdomain.com`

## Step 2 — Supabase custom SMTP

1. Open [Supabase Dashboard](https://supabase.com/dashboard/project/eamkkmlpphsimvznjjcf)
2. **Project Settings** (gear) → **Authentication**
3. Scroll to **SMTP Settings**
4. Toggle **Enable Custom SMTP** ON

| Field | Value |
|-------|--------|
| **Sender email** | `onboarding@resend.dev` (test) or `intel@yourdomain.com` (prod) |
| **Sender name** | `Pricing Sentinel` |
| **Host** | `smtp.resend.com` |
| **Port** | `465` |
| **Username** | `resend` |
| **Password** | your Resend API key (`re_...`) |

5. **Save**

## Step 3 — Email auth settings

Still in **Authentication**:

1. **Providers → Email** — ensure Email is enabled
2. **Email Templates → Magic Link** — optional: edit subject/body to match brand
3. **URL Configuration** — confirm redirect URLs:
   - `http://localhost:3000/auth/callback` (local)
   - `https://YOUR-APP.vercel.app/auth/callback` (production)
   - `https://*.vercel.app/auth/callback` (Vercel previews)

Set **Site URL** to your production app URL. Set **NEXT_PUBLIC_APP_URL** in Vercel to match.

## Step 4 — Test

1. Wait a few minutes after saving SMTP (Supabase propagates settings)
2. Open your app → **Request Access**
3. Enter email → **Send Magic Link** (once only)
4. Check inbox — email should arrive from your Resend sender, not `noreply@mail.app.supabase.io`

If it fails, check **Supabase → Authentication → Logs** for SMTP errors.

## Step 5 — Same Resend key for alert emails (optional)

Add to **GitHub Actions secrets** (for premium alert digests):

- `RESEND_API_KEY` = same `re_...` key
- `RESEND_FROM_EMAIL` = same sender address

## Troubleshooting

| Error | Fix |
|-------|-----|
| Still rate limited | Built-in mailer may still be active — double-check Custom SMTP is ON and saved |
| SMTP authentication failed | Username must be exactly `resend`; password is API key, not account password |
| Resend 403 / email only works for you | Using `onboarding@resend.dev` — **verify a domain** in Resend and update Supabase sender |
| Google sign-in fails | See [google-oauth-setup.md](./google-oauth-setup.md) |
| Link goes to wrong site | Fix Site URL + Redirect URLs in Supabase URL Configuration |

## Alternative: Google sign-in (no email)

See [deployment.md](./deployment.md) — enable Google provider in Supabase; login page has **Sign in with Google** button.
