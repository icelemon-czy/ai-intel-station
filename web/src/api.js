/**
 * Lightweight fetch wrapper shared across components.
 *
 * - Always sends Content-Type: application/json.
 * - Throws `Error` with the server's error body when status is not 2xx.
 */
export async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      if (body && body.message) detail = body.message;
      else if (body && body.error) detail = body.error;
    } catch (_e) {
      // body wasn't JSON; keep status-only message
    }
    throw new Error(detail);
  }
  return response.json();
}