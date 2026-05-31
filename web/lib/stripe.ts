import Stripe from "stripe";

export function getStripe() {
  return new Stripe(process.env.STRIPE_SECRET_KEY!);
}

export async function isPremiumUser(userId: string): Promise<boolean> {
  const { createClient } = await import("@/lib/supabase/server");
  const supabase = await createClient();
  const { data } = await supabase
    .from("subscriptions")
    .select("status, current_period_end")
    .eq("user_id", userId)
    .maybeSingle();

  if (!data || data.status !== "active") return false;
  if (!data.current_period_end) return true;
  return new Date(data.current_period_end) > new Date();
}
