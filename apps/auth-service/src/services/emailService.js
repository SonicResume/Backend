// ─── Resend welcome email ─────────────────────────────
const { Resend } = require("resend");

const resend = new Resend(process.env.RESEND_API_KEY);

/**
 * Send a welcome email after Firebase signup.
 * @param {string} to - recipient email address
 * @param {string} name - user's display name (optional fallback)
 */
async function sendWelcomeEmail(to, name) {
  const displayName = name || "there";
  const subject = "Welcome to Hermes Backend 🚀";
  const html = `
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h1>Hey ${displayName}!</h1>
      <p>Welcome aboard. Your account is all set up and ready to go.</p>
      <p>Here's what you can do:</p>
      <ul>
        <li>Manage your contacts with smart AI tagging</li>
        <li>Upload files (PDFs, docs, images) — auto-summarized</li>
        <li>Manage your billing and subscription</li>
      </ul>
      <hr />
      <p style="color: #666; font-size: 12px;">Hermes Backend — built with 💪</p>
    </div>
  `;

  const { data, error } = await resend.emails.send({
    from: "Hermes <onboarding@yourdomain.com>",
    to,
    subject,
    html,
  });

  if (error) {
    console.error("[Resend] Welcome email failed:", error);
    return { ok: false, error };
  }
  console.log("[Resend] Welcome email sent to", to, data?.id);
  return { ok: true, id: data?.id };
}

module.exports = { sendWelcomeEmail };