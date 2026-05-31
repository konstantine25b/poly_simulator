import { apiGet, apiPatch, apiPost } from "../../../apiClient.js";

export function registerUser(email, password) {
  return apiPost("/auth/register", { email, password });
}

export function loginUser(email, password) {
  return apiPost("/auth/login", { email, password });
}

export function fetchMe(token) {
  return apiGet("/auth/me", token);
}

export function updateProfile(token, username) {
  return apiPatch("/auth/profile", { username }, token);
}

export function resetPassword(token, email, currentPassword, newPassword) {
  return apiPost(
    "/auth/reset-password",
    { email, current_password: currentPassword, new_password: newPassword },
    token,
  );
}

export function deleteOwnAccount(token, password) {
  return apiPost("/auth/delete-account", { password }, token);
}

export function adminRestoreUser(token, userId) {
  return apiPost(`/admin/users/${encodeURIComponent(userId)}/restore`, {}, token);
}
