import Stripe from "stripe";
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: Request) {
  try {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );

    const authHeader = req.headers.get("authorization");

    if (!authHeader) {
      return NextResponse.json({ error: "Not logged in" }, { status: 401 });
    }

    const token = authHeader.replace("Bearer ", "");

    const {
      data: { user },
    } = await supabase.auth.getUser(token);

    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 401 });
    }

    // 🔥 Get Stripe customer from DB
    const { data, error } = await supabase
      .from("subscriptions")
      .select("stripe_customer_id")
      .eq("user_id", user.id)
      .single();

    if (error || !data?.stripe_customer_id) {
      return NextResponse.json(
        { error: "No subscription found" },
        { status: 400 }
      );
    }

    // 🚀 Create billing portal session
    const session = await stripe.billingPortal.sessions.create({
      customer: data.stripe_customer_id,
      return_url: `${process.env.NEXT_PUBLIC_SITE_URL}/account`,
    });

    return NextResponse.json({ url: session.url });

  } catch (err) {
    console.error("Billing portal error:", err);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}

