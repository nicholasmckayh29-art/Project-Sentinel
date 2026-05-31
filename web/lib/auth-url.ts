/** Canonical app origin for auth redirects (must match Supabase URL allow list). */
export function getAppOrigin(fallbackOrigin?: string): string {
  const fromEnv = process.env.NEXT_PUBLIC_APP_URL?.replace(/\/$/, "");
  if (fromEnv) return fromEnv;
  if (fallbackOrigin) return fallbackOrigin.replace(/\/$/, "");
  if (typeof window !== "undefined") return window.location.origin;
  return "http://localhost:3000";
}

export function getAuthCallbackUrl(fallbackOrigin?: string): string {
  return `${getAppOrigin(fallbackOrigin)}/auth/callback`;
}

/** Production-safe redirect base on Vercel (uses x-forwarded-host when needed). */
export function getRedirectOrigin(
  request: Request,
  fallbackOrigin: string
): string {
  const isLocal = process.env.NODE_ENV === "development";
  if (isLocal) return fallbackOrigin.replace(/\/$/, "");

  const fromEnv = process.env.NEXT_PUBLIC_APP_URL?.replace(/\/$/, "");
  if (fromEnv) return fromEnv;

  const forwardedHost = request.headers.get("x-forwarded-host");
  if (forwardedHost) return `https://${forwardedHost}`;

  return fallbackOrigin.replace(/\/$/, "");
}
