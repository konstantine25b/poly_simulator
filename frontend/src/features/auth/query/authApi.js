import { apiBase } from "../../../config.js";

function humanizeField(loc) {
  if (!Array.isArray(loc)) return "";
  const parts = loc.filter((p) => p !== "body");
  if (parts.length === 0) return "";
  return parts.join(".");
}

function formatValidationItem(item) {
  if (!item || typeof item !== "object") return String(item ?? "");
  const field = humanizeField(item.loc);
  const msg = item.msg || item.message || "invalid value";
  return field ? `${field}: ${msg}` : msg;
}

function extractErrorMessage(data, status) {
  if (data && typeof data === "object") {
    const detail = data.detail ?? data.message ?? data.error;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map(formatValidationItem).join("; ");
    }
    if (detail && typeof detail === "object") {
      return formatValidationItem(detail);
    }
  }
  if (status === 422) return "Some fields are invalid. Please check your input.";
  if (status === 401) return "Invalid email or password.";
  if (status === 409) return "Email already registered.";
  if (status === 400) return "Bad request.";
  if (status >= 500) return "Server error. Please try again.";
  return `Request failed (${status})`;
}

async function postJson(path, body, token) {
  let res;
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    res = await fetch(`${apiBase}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
  } catch (e) {
    throw new Error(`Network error: ${e.message || "could not reach server"}`);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(data, res.status));
  return data;
}

async function patchJson(path, body, token) {
  let res;
  try {
    res = await fetch(`${apiBase}${path}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
  } catch (e) {
    throw new Error(`Network error: ${e.message || "could not reach server"}`);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(data, res.status));
  return data;
}

export function registerUser(email, password) {
  return postJson("/auth/register", { email, password });
}

export function loginUser(email, password) {
  return postJson("/auth/login", { email, password });
}

export async function fetchMe(token) {
  const res = await fetch(`${apiBase}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(data, res.status));
  return data;
}

export function updateProfile(token, username) {
  return patchJson("/auth/profile", { username }, token);
}

export function resetPassword(token, email, currentPassword, newPassword) {
  return postJson(
    "/auth/reset-password",
    { email, current_password: currentPassword, new_password: newPassword },
    token,
  );
}
