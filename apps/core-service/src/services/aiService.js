const { Mistral } = require("@mistralai/mistralai");

let client = null;

function getMistralClient() {
  if (client) return client;
  const apiKey = process.env.MISTRAL_API_KEY;
  if (!apiKey) {
    throw new Error("Missing MISTRAL_API_KEY env var");
  }
  client = new Mistral({ apiKey });
  return client;
}

/**
 * Summarise a text chunk (used for file contents, contact notes).
 */
async function summariseText(text) {
  const c = getMistralClient();
  const result = await c.chat.complete({
    model: "mistral-small-latest",
    messages: [
      {
        role: "system",
        content:
          "You are a helpful assistant. Summarise the following content concisely in 2-3 sentences.",
      },
      { role: "user", content: text },
    ],
  });
  return result.choices?.[0]?.message?.content?.trim() || "";
}

/**
 * Generate tags from a text block (used for auto-tagging contacts / files).
 */
async function generateTags(text) {
  const c = getMistralClient();
  const result = await c.chat.complete({
    model: "mistral-small-latest",
    messages: [
      {
        role: "system",
        content:
          "You are a tagging assistant. Return a JSON array of 3-5 single-word tags relevant to the content. Only output the array, e.g. [\"tag1\",\"tag2\"].",
      },
      { role: "user", content: text },
    ],
  });
  const raw = result.choices?.[0]?.message?.content?.trim() || "[]";
  try {
    return JSON.parse(raw);
  } catch {
    return [raw];
  }
}

module.exports = { summariseText, generateTags };