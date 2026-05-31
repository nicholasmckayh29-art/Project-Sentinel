"use client";

import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { useState } from "react";

function friendlyAuthError(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("rate limit") || lower.includes("email rate")) {
    return (
      "EMAIL RATE LIMIT — Supabase's built-in mailer allows ~4 emails/hour. " +
      "Wait 60 minutes, or configure custom SMTP (Resend) in Supabase → Authentication → SMTP Settings."
    );
  }
  return message;
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const supabase = createClient();
    const { error: authError } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    setLoading(false);
    if (authError) {
      setError(friendlyAuthError(authError.message));
      return;
    }
    setSent(true);
  }

  async function handleGoogleLogin() {
    setOauthLoading(true);
    setError(null);
    const supabase = createClient();
    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    setOauthLoading(false);
    if (authError) {
      setError(friendlyAuthError(authError.message));
    }
  }

  return (
    <main className="flex-1 flex items-center justify-center px-6 py-16">
      <div className="w-full max-w-md card-terminal p-8 space-y-6">
        <div>
          <p className="badge-classified mb-3">AUTH REQUIRED</p>
          <h1 className="font-mono text-xl text-accent terminal-glow">SECURE LOGIN</h1>
          <p className="text-sm text-muted mt-2">
            Magic link or Google. No passwords stored.
          </p>
        </div>

        {sent ? (
          <p className="font-mono text-sm text-accent">
            &gt; TRANSMISSION SENT. CHECK YOUR EMAIL.
          </p>
        ) : (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="font-mono text-xs text-muted block mb-1">EMAIL</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface-elevated border border-border px-3 py-2 font-mono text-sm focus:border-accent outline-none"
                placeholder="agent@domain.com"
              />
            </div>
            {error && (
              <p className="text-alert-increase font-mono text-xs leading-relaxed">{error}</p>
            )}
            <button
              type="submit"
              disabled={loading || oauthLoading}
              className="w-full font-mono text-sm bg-accent text-background py-3 hover:bg-accent-dim disabled:opacity-50 tracking-wider"
            >
              {loading ? "TRANSMITTING..." : "SEND MAGIC LINK"}
            </button>
          </form>
        )}

        {!sent && (
          <>
            <div className="font-mono text-xs text-muted text-center">— OR —</div>
            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={loading || oauthLoading}
              className="w-full font-mono text-sm border border-border py-3 hover:border-accent hover:text-accent disabled:opacity-50 tracking-wider"
            >
              {oauthLoading ? "CONNECTING..." : "SIGN IN WITH GOOGLE"}
            </button>
          </>
        )}

        <Link href="/" className="font-mono text-xs text-muted hover:text-accent block">
          ← BACK
        </Link>
      </div>
    </main>
  );
}
