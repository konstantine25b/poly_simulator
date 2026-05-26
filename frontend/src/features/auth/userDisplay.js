export function displayName(user) {
  if (!user) return "";
  const username = user.username && String(user.username).trim();
  if (username) return username;
  return user.email || "";
}

export function displayInitial(user) {
  return displayName(user).trim().charAt(0).toUpperCase() || "?";
}
