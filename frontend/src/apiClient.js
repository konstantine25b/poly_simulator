import { apiBase } from "./config.js";

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

export function extractErrorMessage(data, status) {
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

async function parseResponse(res) {
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(extractErrorMessage(data, res.status));
  return data;
}

function authHeaders(token, json) {
  const headers = {};
  if (json) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function request(method, path, { body, token } = {}) {
  const opts = { method, headers: authHeaders(token, body !== undefined) };
  if (body !== undefined) opts.body = JSON.stringify(body);
  let res;
  try {
    res = await fetch(`${apiBase}${path}`, opts);
  } catch (e) {
    throw new Error(`Network error: ${e.message || "could not reach server"}`);
  }
  return parseResponse(res);
}

export function apiGet(path, token) {
  return request("GET", path, { token });
}

export function apiPost(path, body, token) {
  return request("POST", path, { body: body ?? {}, token });
}

export function apiPatch(path, body, token) {
  return request("PATCH", path, { body, token });
}

export function apiDelete(path, token) {
  return request("DELETE", path, { token });
}
