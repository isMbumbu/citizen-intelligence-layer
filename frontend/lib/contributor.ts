/**
 * Anonymous contributor reference for citizen submissions.
 *
 * The backend requires a UUID for comment authors, comment reporters, and
 * evidence uploaders, but there is no sign-in flow. Rather than asking citizens
 * to invent a UUID, the browser generates one once and reuses it, so a person's
 * submissions stay linked without collecting any identifying information.
 */

const storageKey = "civicact-contributor-id";

function newUuid(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  // randomUUID is limited to secure contexts; build a v4 UUID by hand otherwise.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function getContributorId(): string {
  try {
    const saved = window.localStorage.getItem(storageKey);
    if (saved) return saved;
    const created = newUuid();
    window.localStorage.setItem(storageKey, created);
    return created;
  } catch {
    // Storage can be unavailable (private mode, blocked cookies); fall back to a
    // per-submission reference rather than blocking the citizen.
    return newUuid();
  }
}
