const Stripe = require("stripe");
const prisma = require("@hermes/prisma");
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

// ─── Stripe price IDs (set these in .env) ─────────────
const PRICE_MONTHLY = process.env.STRIPE_PRICE_MONTHLY || "price_monthly";
const PRICE_YEARLY = process.env.STRIPE_PRICE_YEARLY || "price_yearly";

/**
 * Create a Stripe Checkout Session for a new subscription.
 * On success, customer is redirected to Stripe's hosted checkout.
 */
async function createCheckoutSession(userId, priceId, successUrl, cancelUrl) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw new Error("User not found");

  // Reuse existing Stripe customer if available
  const sub = await prisma.subscription.findUnique({ where: { userId } });
  let customerId = sub?.stripeCustomerId;

  const session = await stripe.checkout.sessions.create({
    mode: "subscription",
    payment_method_types: ["card"],
    line_items: [{ price: priceId, quantity: 1 }],
    customer: customerId,
    customer_email: customerId ? undefined : user.email,
    success_url: successUrl,
    cancel_url: cancelUrl,
    metadata: { userId },
  });

  // Store Stripe customer + session ref
  await prisma.subscription.upsert({
    where: { userId },
    update: { stripeCustomerId: session.customer },
    create: {
      userId,
      stripeCustomerId: session.customer,
      status: "incomplete",
    },
  });

  return session;
}

/**
 * Handle Stripe webhook events (idempotent).
 */
async function handleWebhookEvent(event) {
  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object;
      const userId = session.metadata?.userId;
      if (!userId) break;

      await prisma.subscription.upsert({
        where: { userId },
        update: {
          stripeCustomerId: session.customer,
          stripeSubscriptionId: session.subscription,
          status: "active",
        },
        create: {
          userId,
          stripeCustomerId: session.customer,
          stripeSubscriptionId: session.subscription,
          status: "active",
        },
      });
      break;
    }

    case "customer.subscription.updated":
    case "customer.subscription.deleted": {
      const sub = event.data.object;
      const dbSub = await prisma.subscription.findUnique({
        where: { stripeSubscriptionId: sub.id },
      });
      if (!dbSub) break;

      await prisma.subscription.update({
        where: { id: dbSub.id },
        data: {
          status: sub.status,
          planId: sub.items?.data?.[0]?.price?.id,
          currentPeriodStart: sub.current_period_start
            ? new Date(sub.current_period_start * 1000)
            : undefined,
          currentPeriodEnd: sub.current_period_end
            ? new Date(sub.current_period_end * 1000)
            : undefined,
        },
      });
      break;
    }

    case "invoice.payment_succeeded": {
      const invoice = event.data.object;
      const subscriptionId = invoice.subscription;
      if (!subscriptionId) break;

      const dbSub = await prisma.subscription.findUnique({
        where: { stripeSubscriptionId: subscriptionId },
      });
      if (!dbSub) break;

      await prisma.subscription.update({
        where: { id: dbSub.id },
        data: { status: "active" },
      });
      break;
    }

    case "invoice.payment_failed": {
      const failedInvoice = event.data.object;
      const subId = failedInvoice.subscription;
      if (!subId) break;

      const dbSub2 = await prisma.subscription.findUnique({
        where: { stripeSubscriptionId: subId },
      });
      if (!dbSub2) break;

      await prisma.subscription.update({
        where: { id: dbSub2.id },
        data: { status: "past_due" },
      });
      break;
    }
  }
}

module.exports = { createCheckoutSession, handleWebhookEvent, PRICE_MONTHLY, PRICE_YEARLY };