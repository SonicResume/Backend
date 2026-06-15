import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { createClient } from "@supabase/supabase-js";

export const dynamic = "force-dynamic";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: NextRequest) {
  try {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );

    const body = await req.text();
    const signature = req.headers.get("stripe-signature");

    if (!signature) {
      return new NextResponse("Missing stripe-signature", { status: 400 });
    }

    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

    const event = stripe.webhooks.constructEvent(
      body,
      signature,
      webhookSecret
    );

    // ✅ PAYMENT SUCCESS
    if (event.type === "checkout.session.completed") {
      const session = event.data.object as Stripe.Checkout.Session;

      const userId = session.metadata?.user_id;

      if (!userId) {
        console.log("❌ No user_id in metadata");
        return NextResponse.json({ received: true });
      }

      console.log("✅ PAYMENT SUCCESS FOR USER:", userId);

      const { error } = await supabase
        .from("subscriptions")
        .upsert(
          {
            user_id: userId,
            stripe_customer_id: session.customer,
            stripe_subscription_id: session.subscription,
            status: "active",
            plan: session.metadata?.plan || "premium",
          },
          { onConflict: "user_id" }
        );

      if (error) {
        console.error("❌ Supabase error:", error);
      } else {
        console.log("✅ Subscription saved");
      }
    }

    return NextResponse.json({ received: true });

  } catch (error) {
    console.error("🔥 Stripe webhook error:", error);
    return new NextResponse("Webhook Error", { status: 400 });
  }
}