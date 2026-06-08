const { Router } = require("express");
const prisma = require("@hermes/prisma");
const { requireAuth } = require("../middleware/firebaseAuth");
const { createCheckoutSession, PRICE_MONTHLY, PRICE_YEARLY } = require("../services/stripeService");

const router = Router();

// ─── Create a Stripe Checkout session ─────────────────
// POST /api/billing/create-checkout
// Body: { priceId?: "price_monthly" | "price_yearly" }
router.post("/create-checkout", requireAuth, async (req, res) => {
  try {
    const priceId = req.body.priceId || PRICE_MONTHLY;
    const successUrl = req.body.successUrl || "https://your-app.com/billing/success";
    const cancelUrl = req.body.cancelUrl || "https://your-app.com/billing/cancel";

    const session = await createCheckoutSession(
      req.userId,
      priceId,
      successUrl,
      cancelUrl
    );

    res.json({ url: session.url, sessionId: session.id });
  } catch (err) {
    console.error("[Billing] create-checkout error:", err);
    res.status(500).json({ error: "Failed to create checkout session" });
  }
});

// ─── Get user's subscription ──────────────────────────
// GET /api/billing/subscription
router.get("/subscription", requireAuth, async (req, res) => {
  const sub = await prisma.subscription.findUnique({ where: { userId: req.userId } });
  if (!sub) return res.json({ subscription: null });
  res.json({ subscription: sub });
});

// ─── List all billing history (invoices) ──────────────
// GET /api/billing/invoices
router.get("/invoices", requireAuth, async (req, res) => {
  const sub = await prisma.subscription.findUnique({ where: { userId: req.userId } });
  if (!sub?.stripeCustomerId) return res.json({ invoices: [] });

  // For a full implementation, fetch from Stripe API:
  // const invoices = await stripe.invoices.list({ customer: sub.stripeCustomerId });
  res.json({ invoices: [] }); // placeholder
});

module.exports = router;