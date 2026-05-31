"use client";

import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function SettingsPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [premium, setPremium] = useState(false);
  const [emailAlerts, setEmailAlerts] = useState(true);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      setEmail(user?.email ?? null);

      if (user) {
        const { data: sub } = await supabase
          .from("subscriptions")
          .select("status, current_period_end")
          .eq("user_id", user.id)
          .maybeSingle();
        setPremium(
          sub?.status === "active" &&
            (!sub.current_period_end || new Date(sub.current_period_end) > new Date())
        );

        const { data: prefs } = await supabase
          .from("notification_prefs")
          .select("email_alerts")
          .eq("user_id", user.id)
          .maybeSingle();
        if (prefs) setEmailAlerts(prefs.email_alerts);
      }
    }
    load();
  }, []);

  async function toggleEmailAlerts() {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;
    const next = !emailAlerts;
    await supabase
      .from("notification_prefs")
      .update({ email_alerts: next })
      .eq("user_id", user.id);
    setEmailAlerts(next);
  }

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/");
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <p className="badge-classified inline-block mb-2">CONFIG</p>
        <h1 className="font-mono text-2xl text-accent terminal-glow">SETTINGS</h1>
      </div>

      <div className="card-terminal p-4 space-y-2 font-mono text-sm">
        <p><span className="text-muted">OPERATOR:</span> {email ?? "—"}</p>
        <p>
          <span className="text-muted">CLEARANCE:</span>{" "}
          <span className={premium ? "text-accent" : "text-muted"}>
            {premium ? "LEVEL 2 — PREMIUM" : "LEVEL 1 — FREE"}
          </span>
        </p>
      </div>

      {!premium && (
        <Link
          href="/pricing"
          className="inline-block font-mono text-sm bg-accent text-background px-4 py-2 tracking-wider"
        >
          REQUEST CLEARANCE UPGRADE
        </Link>
      )}

      <label className="flex items-center gap-3 font-mono text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={emailAlerts}
          onChange={toggleEmailAlerts}
          disabled={!premium}
          className="accent-accent"
        />
        Email alert delivery {premium ? "" : "(premium only)"}
      </label>

      <button
        type="button"
        onClick={signOut}
        className="font-mono text-sm border border-border px-4 py-2 hover:border-alert-increase hover:text-alert-increase"
      >
        TERMINATE SESSION
      </button>
    </div>
  );
}
