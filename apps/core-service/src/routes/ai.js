const { Router } = require("express");
const { requireAuth } = require("../middleware/firebaseAuth");
const { summariseText, generateTags } = require("../services/aiService");

const router = Router();
router.use(requireAuth);

// ─── Generic text summarisation ──────────────────────
// POST /api/ai/summarise  { text }
router.post("/summarise", async (req, res) => {
  const { text } = req.body;
  if (!text || typeof text !== "string") {
    return res.status(400).json({ error: "text field is required" });
  }
  const summary = await summariseText(text.slice(0, 20_000));
  res.json({ summary });
});

// ─── Generic tag generation ──────────────────────────
// POST /api/ai/tags  { text }
router.post("/tags", async (req, res) => {
  const { text } = req.body;
  if (!text || typeof text !== "string") {
    return res.status(400).json({ error: "text field is required" });
  }
  const tags = await generateTags(text.slice(0, 20_000));
  res.json({ tags });
});

module.exports = router;