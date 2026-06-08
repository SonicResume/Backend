const admin = require("firebase-admin");
const prisma = require("@hermes/prisma");

function getFirebaseAdmin() {
  if (admin.apps.length) return admin;
  admin.initializeApp({
    credential: admin.credential.cert({
      projectId: process.env.FIREBASE_PROJECT_ID,
      clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
      privateKey: (process.env.FIREBASE_PRIVATE_KEY || "").replace(/\\n/g, "\n"),
    }),
    storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
  });
  return admin;
}

/**
 * Verify Firebase ID token, then resolve the local User.id
 * and attach it to req.userId. Rejects if user hasn't synced yet.
 */
async function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing or invalid Authorization header" });
  }

  const token = authHeader.split("Bearer ")[1];

  try {
    const decoded = await getFirebaseAdmin().auth().verifyIdToken(token);

    // Resolve local user
    const user = await prisma.user.findUnique({
      where: { firebaseUid: decoded.uid },
    });
    if (!user) {
      return res.status(404).json({ error: "User not synced. Call POST /api/auth/sync first." });
    }

    req.userId = user.id;
    next();
  } catch (err) {
    console.error("[Core-Auth] Token verification failed:", err.code || err.message);
    return res.status(401).json({ error: "Invalid or expired token" });
  }
}

module.exports = { requireAuth };