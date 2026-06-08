const admin = require("firebase-admin");

// ─── Lazy-init Firebase Admin SDK ─────────────────────
let firebaseApp = null;

function getFirebaseAdmin() {
  if (firebaseApp) return admin;

  const projectId = process.env.FIREBASE_PROJECT_ID;
  const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
  const privateKey = process.env.FIREBASE_PRIVATE_KEY;

  if (!projectId || !clientEmail || !privateKey) {
    throw new Error(
      "Missing Firebase Admin env vars: FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY"
    );
  }

  admin.initializeApp({
    credential: admin.credential.cert({
      projectId,
      clientEmail,
      privateKey: privateKey.replace(/\\n/g, "\n"),
    }),
  });

  firebaseApp = admin;
  return admin;
}

// ─── Express middleware: verify Firebase ID token ──────
function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing or invalid Authorization header" });
  }

  const token = authHeader.split("Bearer ")[1];

  getFirebaseAdmin()
    .auth()
    .verifyIdToken(token)
    .then((decoded) => {
      req.firebaseUser = decoded; // { uid, email, name, picture, ... }
      next();
    })
    .catch((err) => {
      console.error("[Firebase] Token verification failed:", err.code || err.message);
      return res.status(401).json({ error: "Invalid or expired token" });
    });
}

module.exports = { getFirebaseAdmin, requireAuth };