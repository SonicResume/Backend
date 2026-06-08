const { Router } = require("express");
const Stripe = require("stripe");
const { handleWebhookEvent } = require("../services/stripeService");

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
const router = Router();

// ─── Stripe webhook (needs raw body for signature verification) ─
// POST /api/billing/webhook
router.post(
  "/webhook", (req, res, next) => {
    // Capture raw body before JSON parsing
    let data = "";
    req.on("data", (chunk) => (data += chunk));
    req.on("end", () => {
      req.rawBody = data;
      next();
    });
  },
  async (req, res) => {
    const sig = req.headers["stripe-signature"];
    const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

    if (!endpointSecret) {
      return res.status(500).json({ error: "STRIPE_WEBHOOK_SECRET not configured" });
    }

    let event;
    try {
      event = stripe.webhooks.constructEvent(req.rawBody, sig, endpointSecret);
    } catch (err) {
      console.error("[Stripe] Webhook signature verification failed:", err.message);
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    try {
      await handleWebhookEvent(event);
    } catch (err) {
      console.error("[Stripe] Webhook handler error:", err);
    }

    res.json({ received: true });
  }
);

module.exports = router;