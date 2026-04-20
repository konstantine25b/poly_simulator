import { apiBase } from "../../../config.js";

async function authedGet(token, path) {
  const res = await fetch(`${apiBase}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data && (data.detail || data.message);
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return data;
}

async function authedPost(token, path, body) {
  const res = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data && (data.detail || data.message);
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return data;
}

export function fetchPortfolios(token) {
  return authedGet(token, "/portfolios");
}

export function fetchPortfolioSummary(token, portfolioRef) {
  return authedGet(token, `/portfolios/${encodeURIComponent(portfolioRef)}/summary`);
}

export function createPortfolio(token, body) {
  return authedPost(token, "/portfolios", body);
}

export function fetchAdminUsers(token) {
  return authedGet(token, "/admin/users");
}
