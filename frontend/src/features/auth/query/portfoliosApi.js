import { apiDelete, apiGet, apiPost } from "../../../apiClient.js";

export function fetchPortfolios(token) {
  return apiGet("/portfolios", token);
}

export function fetchPortfolioSummary(token, portfolioRef) {
  return apiGet(`/portfolios/${encodeURIComponent(portfolioRef)}/summary`, token);
}

export function fetchPortfolioPositions(token, portfolioRef) {
  return apiGet(`/portfolios/${encodeURIComponent(portfolioRef)}/positions`, token);
}

export function fetchPortfolioTrades(token, portfolioRef) {
  return apiGet(`/portfolios/${encodeURIComponent(portfolioRef)}/trades`, token);
}

export function createPortfolio(token, body) {
  return apiPost("/portfolios", body, token);
}

export function fetchAdminUsers(token) {
  return apiGet("/admin/users", token);
}

export function deletePortfolio(token, portfolioRef) {
  return apiDelete(`/portfolios/${encodeURIComponent(portfolioRef)}`, token);
}

export function placeBet(token, portfolioRef, body) {
  return apiPost(`/portfolios/${encodeURIComponent(portfolioRef)}/bet`, body, token);
}

export function closePosition(token, portfolioRef, body) {
  return apiPost(`/portfolios/${encodeURIComponent(portfolioRef)}/close`, body, token);
}

export function settlePosition(token, portfolioRef, body) {
  return apiPost(`/portfolios/${encodeURIComponent(portfolioRef)}/settle`, body, token);
}
