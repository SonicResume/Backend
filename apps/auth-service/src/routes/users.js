const { Router } = require("express");
const prisma = require("@hermes/prisma");
const { requireAuth } = require("../middleware/firebaseAuth");
const { sendWelcomeEmail } = require("../services/emailService");

const router = Router();

// ─── Sync / Register user from Firebase token ─────────
// POST /api/auth/sync
router.post("/sync", requireAuth, async (req, res) => {
  try {
    const { uid, email, name, picture } = req.firebaseUser;

    const user = await prisma.user.upsert({
      where: { firebaseUid: uid },
      update: { email, displayName: name, photoUrl: picture },
      create: { firebaseUid: uid, email, displayName: name, photoUrl: picture },
    });

    // Send welcome email on first signup (newly created)
    // `createdAt` check: if it equals `updatedAt`, it's a fresh insert
    if (user.createdAt.getTime() === user.updatedAt.getTime() && email) {
      sendWelcomeEmail(email, name).catch((e) =>
        console.error("[Auth] Welcome email async error:", e)
      );
    }

    res.json({ user });
  } catch (err) {
    console.error("[Auth] POST /sync error:", err);
    res.status(500).json({ error: "Failed to sync user" });
  }
});

// ─── Get current user profile ─────────────────────────
// GET /api/auth/me
router.get("/me", requireAuth, async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { firebaseUid: req.firebaseUser.uid },
    });
    if (!user) return res.status(404).json({ error: "User not found" });
    res.json({ user });
  } catch (err) {
    console.error("[Auth] GET /me error:", err);
    res.status(500).json({ error: "Failed to fetch user" });
  }
});

module.exports = router;