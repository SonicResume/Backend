const admin = require("firebase-admin");

/**
 * Safe Firebase initialization
 */
function getFirebaseStorage() {
  try {
    // Prevent crash if env is missing
    if (
      !process.env.FIREBASE_PROJECT_ID ||
      !process.env.FIREBASE_CLIENT_EMAIL ||
      !process.env.FIREBASE_PRIVATE_KEY ||
      !process.env.FIREBASE_STORAGE_BUCKET
    ) {
      console.warn(
        "[Firebase] Missing env vars. Storage service disabled."
      );
      return null;
    }

    if (!admin.apps.length) {
      admin.initializeApp({
        credential: admin.credential.cert({
          projectId: process.env.FIREBASE_PROJECT_ID,
          clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
          privateKey: process.env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, "\n"),
        }),
        storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
      });
    }

    return admin.storage().bucket();
  } catch (err) {
    console.warn("[Firebase] Initialization failed:", err.message);
    return null;
  }
}

const bucket = getFirebaseStorage();

/**
 * Upload a buffer/stream to Firebase Storage.
 * Returns null if storage is not available.
 */
async function uploadFile(userId, fileName, buffer, mimeType) {
  if (!bucket) {
    console.warn("[Firebase] upload skipped (no bucket)");
    return {
      storagePath: null,
      publicUrl: null,
    };
  }

  const destPath = `users/${userId}/files/${Date.now()}_${fileName}`;
  const file = bucket.file(destPath);

  await file.save(buffer, {
    metadata: { contentType: mimeType },
  });

  await file.makePublic();

  const publicUrl = `https://storage.googleapis.com/${bucket.name}/${destPath}`;

  return {
    storagePath: destPath,
    publicUrl,
  };
}

/**
 * Delete a file from Firebase Storage.
 */
async function deleteFile(storagePath) {
  if (!bucket || !storagePath) {
    console.warn("[Firebase] delete skipped");
    return;
  }

  await bucket.file(storagePath).delete();
}

module.exports = {
  uploadFile,
  deleteFile,
};
