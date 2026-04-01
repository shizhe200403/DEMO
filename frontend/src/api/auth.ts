import http from "./http";

export async function login(account: string, password: string) {
  const { data } = await http.post("/accounts/login/", { account, password });
  return data;
}

export async function register(payload: Record<string, unknown>) {
  const { data } = await http.post("/accounts/register/", payload);
  return data;
}

export async function getMe() {
  const { data } = await http.get("/accounts/me/");
  return data;
}

export async function updateMe(payload: Record<string, unknown>) {
  const { data } = await http.put("/accounts/me/", payload);
  return data;
}

export async function updateProfile(payload: Record<string, unknown>) {
  const { data } = await http.put("/accounts/me/profile/", payload);
  return data;
}

export async function updateHealthCondition(payload: Record<string, unknown>) {
  const { data } = await http.put("/accounts/me/health-condition/", payload);
  return data;
}

export async function updateFullProfile(payload: Record<string, unknown>) {
  const { data } = await http.put("/accounts/me/full-profile/", payload);
  return data;
}

export async function changePassword(payload: { old_password: string; new_password: string }) {
  const { data } = await http.post("/accounts/me/change-password/", payload);
  return data;
}

export async function deleteAccount(payload: { password: string }) {
  const { data } = await http.post("/accounts/me/delete/", payload);
  return data;
}

