const { Router } = require("express");
const multer = require("multer");
const prisma = require("@hermes/prisma");
const { requireAuth } = require("../middleware/firebaseAuth");
const { uploadFile, deleteFile } = require("../services/storageService");
const { summariseText, generateTags } = require("../services/aiService");

const router = Router();
router.use(requireAuth);

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 20 * 1024 * 1024 } });

// ─── List user's files ───────────────────────────────
// GET /api/files
router.get("/", async (req, res) => {
  const files = await prisma.file.findMany({
    where: { userId: req.userId },
    orderBy: { createdAt: "desc" },
  });
  res.json({ files });
});

// ─── Upload a file ───────────────────────────────────
// POST /api/files/upload
router.post("/upload", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No file provided" });

  const { originalname, buffer, mimetype, size } = req.file;

  // Upload to Firebase Storage
  const { storagePath, publicUrl } = await uploadFile(req.userId, originalname, buffer, mimetype);

  // Extract text content for AI processing (simple text/plain for now;
  // PDFs / DOCX would need a parsing lib — extend as needed)
  let content = "";
  if (mimetype === "text/plain") {
    content = buffer.toString("utf-8").slice(0, 10_000);
  }

  let aiSummary = null;
  let aiTags = [];
  if (content) {
    try {
      [aiSummary, aiTags] = await Promise.all([
        summariseText(content),
        generateTags(content),
      ]);
    } catch (e) {
      console.error("[AI] File processing error:", e.message);
    }
  } else {
    // For non-text files, tag based on filename
    try {
      aiTags = await generateTags(originalname.replace(/\.\w+$/, "").replace(/[-_]/g, " "));
    } catch {
      // non-critical
    }
  }

  const file = await prisma.file.create({
    data: {
      userId: req.userId,
      originalName: originalname,
      storagePath,
      mimeType: mimetype,
      size,
      aiSummary,
      aiTags,
    },
  });

  res.status(201).json({ file, publicUrl });
});

// ─── Delete a file ───────────────────────────────────
// DELETE /api/files/:id
router.delete("/:id", async (req, res) => {
  const file = await prisma.file.findFirst({
    where: { id: req.params.id, userId: req.userId },
  });
  if (!file) return res.status(404).json({ error: "File not found" });

  await deleteFile(file.storagePath);
  await prisma.file.delete({ where: { id: file.id } });

  res.json({ ok: true });
});

module.exports = router;