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

export async function uploadAvatar(file: File) {
  const form = new FormData();
  form.append("avatar", file);
  const { data } = await http.post("/accounts/me/avatar/", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getSecurityQuestions() {
  const { data } = await http.get("/accounts/security-questions/");
  return data;
}

export async function setSecurityQuestion(payload: { question: string; answer: string }) {
  const { data } = await http.post("/accounts/me/security-question/", payload);
  return data;
}

export async function getSecurityQuestion(account: string) {
  const { data } = await http.post("/accounts/get-security-question/", { account });
  return data;
}

export async function resetPasswordBySecurity(payload: { account: string; answer: string; new_password: string }) {
  const { data } = await http.post("/accounts/reset-password/", payload);
  return data;
}
