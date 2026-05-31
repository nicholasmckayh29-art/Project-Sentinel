import { getStripe } from "@/lib/stripe";
import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";
import type Stripe from "stripe";

function adminSupabase() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

export async function POST(request: Request) {
  const body = await request.text();
  const sig = request.headers.get("stripe-signature");
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!sig || !webhookSecret) {
    return NextResponse.json({ error: "Webhook not configured" }, { status: 400 });
  }

  const stripe = getStripe();
  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, sig, webhookSecret);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Invalid signature";
    return NextResponse.json({ error: message }, { status: 400 });
  }

  const supabase = adminSupabase();

  if (
    event.type === "checkout.session.completed" ||
    event.type === "customer.subscription.updated" ||
    event.type === "customer.subscription.deleted"
  ) {
    const subscription =
      event.type === "checkout.session.completed"
        ? await stripe.subscriptions.retrieve(
            (event.data.object as Stripe.Checkout.Session).subscription as string
          )
        : (event.data.object as Stripe.Subscription);

    const userId = subscription.metadata.supabase_user_id;
    if (!userId) {
      return NextResponse.json({ received: true });
    }

    const status =
      subscription.status === "active" || subscription.status === "trialing"
        ? "active"
        : "inactive";

    const periodEnd =
      "current_period_end" in subscription && typeof subscription.current_period_end === "number"
        ? new Date(subscription.current_period_end * 1000).toISOString()
        : null;

    await supabase.from("subscriptions").upsert(
      {
        user_id: userId,
        source: "stripe",
        stripe_customer_id: subscription.customer as string,
        stripe_subscription_id: subscription.id,
        status,
        product_id: subscription.items.data[0]?.price.id,
        current_period_end: periodEnd,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "user_id" }
    );
  }

  return NextResponse.json({ received: true });
}
