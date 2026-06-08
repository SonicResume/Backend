const { Router } = require("express");
const prisma = require("@hermes/prisma");
const { requireAuth } = require("../middleware/firebaseAuth");
const { summariseText, generateTags } = require("../services/aiService");

const router = Router();

// ─── All contact routes require auth ─────────────────
router.use(requireAuth);

// ─── List contacts (paginated) ───────────────────────
// GET /api/contacts?page=1&limit=20
router.get("/", async (req, res) => {
  const page = Math.max(1, parseInt(req.query.page, 10) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(req.query.limit, 10) || 20));
  const skip = (page - 1) * limit;

  const [contacts, total] = await Promise.all([
    prisma.contact.findMany({
      where: { userId: req.userId },
      skip,
      take: limit,
      orderBy: { updatedAt: "desc" },
    }),
    prisma.contact.count({ where: { userId: req.userId } }),
  ]);

  res.json({ contacts, total, page, limit });
});

// ─── Get single contact ──────────────────────────────
// GET /api/contacts/:id
router.get("/:id", async (req, res) => {
  const contact = await prisma.contact.findFirst({
    where: { id: req.params.id, userId: req.userId },
  });
  if (!contact) return res.status(404).json({ error: "Contact not found" });
  res.json({ contact });
});

// ─── Create contact + optional AI tagging ────────────
// POST /api/contacts
router.post("/", async (req, res) => {
  const { firstName, lastName, email, phone, company, jobTitle, notes } = req.body;
  if (!firstName) return res.status(400).json({ error: "firstName is required" });

  let tags = [];
  // Auto-generate tags from all contact data if no explicit tags
  const textToTag = [firstName, lastName, company, jobTitle, notes]
    .filter(Boolean)
    .join(" ");
  if (textToTag.length > 10) {
    try {
      tags = await generateTags(textToTag);
    } catch (e) {
      console.error("[AI] Tag generation failed:", e.message);
    }
  }

  const contact = await prisma.contact.create({
    data: {
      userId: req.userId,
      firstName,
      lastName,
      email,
      phone,
      company,
      jobTitle,
      notes,
      tags,
    },
  });

  res.status(201).json({ contact });
});

// ─── Update contact ───────────────────────────────────
// PATCH /api/contacts/:id
router.patch("/:id", async (req, res) => {
  const existing = await prisma.contact.findFirst({
    where: { id: req.params.id, userId: req.userId },
  });
  if (!existing) return res.status(404).json({ error: "Contact not found" });

  const allowed = ["firstName", "lastName", "email", "phone", "company", "jobTitle", "notes", "tags"];
  const data = {};
  for (const key of allowed) {
    if (req.body[key] !== undefined) data[key] = req.body[key];
  }

  const contact = await prisma.contact.update({
    where: { id: req.params.id },
    data,
  });

  res.json({ contact });
});

// ─── Delete contact ───────────────────────────────────
// DELETE /api/contacts/:id
router.delete("/:id", async (req, res) => {
  const existing = await prisma.contact.findFirst({
    where: { id: req.params.id, userId: req.userId },
  });
  if (!existing) return res.status(404).json({ error: "Contact not found" });

  await prisma.contact.delete({ where: { id: req.params.id } });
  res.json({ ok: true });
});

// ─── Summarise contact notes via Mistral ─────────────
// POST /api/contacts/:id/summarise
router.post("/:id/summarise", async (req, res) => {
  const contact = await prisma.contact.findFirst({
    where: { id: req.params.id, userId: req.userId },
  });
  if (!contact) return res.status(404).json({ error: "Contact not found" });

  const text = [contact.firstName, contact.lastName, contact.company, contact.notes]
    .filter(Boolean)
    .join(" ");
  if (!text) return res.status(400).json({ error: "Nothing to summarise" });

  const summary = await summariseText(text);
  res.json({ summary });
});

module.exports = router;