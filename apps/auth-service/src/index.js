const express = require("express");
const cors = require("cors");
const userRoutes = require("./routes/users");

const PORT = process.env.AUTH_SERVICE_PORT || 4001;

const app = express();
app.use(cors());
app.use(express.json());

// ─── Routes ───────────────────────────────────────────
app.use("/api/auth", userRoutes);

// ─── Health ───────────────────────────────────────────
app.get("/health", (_req, res) => res.json({ ok: true, service: "auth" }));

// ─── Start ────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[Auth Service] running on http://localhost:${PORT}`);
  console.log(`  POST /api/auth/sync  — sync Firebase user + send welcome email`);
  console.log(`  GET  /api/auth/me    — get current user profile`);
  console.log(`  GET  /health         — health check`);
});