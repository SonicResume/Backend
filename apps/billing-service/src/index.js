const express = require("express");
const cors = require("cors");
const paymentRoutes = require("./routes/payments");
const webhookRoutes = require("./routes/webhooks");

const PORT = process.env.BILLING_SERVICE_PORT || 4003;

const app = express();

// ─── Webhook route needs raw body — register BEFORE json middleware ─
app.use("/api/billing", webhookRoutes);

// ─── Everything else is JSON ─────────────────────────
app.use(cors());
app.use(express.json());

app.use("/api/billing", paymentRoutes);

// ─── Health ───────────────────────────────────────────
app.get("/health", (_req, res) => res.json({ ok: true, service: "billing" }));

// ─── Start ────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[Billing Service] running on http://localhost:${PORT}`);
  console.log(`  POST /api/billing/create-checkout  — new Stripe checkout session`);
  console.log(`  GET  /api/billing/subscription     — current subscription`);
  console.log(`  GET  /api/billing/invoices         — invoice history`);
  console.log(`  POST /api/billing/webhook          — Stripe webhook`);
  console.log(`  GET  /health                       — health check`);
});