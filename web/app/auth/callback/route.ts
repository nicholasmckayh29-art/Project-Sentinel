import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";
import { getRedirectOrigin } from "@/lib/auth-url";

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  let next = searchParams.get("next") ?? "/onboarding";
  if (!next.startsWith("/")) {
    next = "/onboarding";
  }

  const base = getRedirectOrigin(request, origin);

  const oauthError = searchParams.get("error_description") ?? searchParams.get("error");
  if (oauthError && !code) {
    return NextResponse.redirect(
      `${base}/login?error=auth&message=${encodeURIComponent(oauthError)}`
    );
  }

  if (code) {
    const cookieStore = await cookies();
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return cookieStore.getAll();
          },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          },
        },
      }
    );

    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      const response = NextResponse.redirect(`${base}${next}`);
      response.cookies.set("ps_session", "1", {
        maxAge: 60 * 60 * 24 * 365,
        path: "/",
        sameSite: "lax",
      });
      return response;
    }

    return NextResponse.redirect(
      `${base}/login?error=auth&message=${encodeURIComponent(error.message)}`
    );
  }

  return NextResponse.redirect(`${base}/login?error=auth&message=missing_code`);
}
