const express = require("express");
const cors = require("cors");
const contactRoutes = require("./routes/contacts");
const fileRoutes = require("./routes/files");
const aiRoutes = require("./routes/ai");

const PORT = process.env.CORE_SERVICE_PORT || 4002;

const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));

// ─── Routes ───────────────────────────────────────────
app.use("/api/contacts", contactRoutes);
app.use("/api/files", fileRoutes);
app.use("/api/ai", aiRoutes);

// ─── Health ───────────────────────────────────────────
app.get("/health", (_req, res) => res.json({ ok: true, service: "core" }));

// ─── Start ────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[Core Service] running on http://localhost:${PORT}`);
  console.log(`  /api/contacts      — CRUD contacts (with AI tagging)`);
  console.log(`  /api/files         — upload / list / delete files`);
  console.log(`  /api/ai            — misc text summarisation + tagging`);
  console.log(`  /health            — health check`);
});