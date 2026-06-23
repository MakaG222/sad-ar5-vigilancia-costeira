import { API } from "../constants.js";

export async function get(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getSafe(path, fallback = null) {
  try {
    return await get(path);
  } catch {
    return fallback;
  }
}

export async function post(path, body) {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
