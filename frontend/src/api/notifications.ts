import http from "./http";

export async function listNotifications() {
  const { data } = await http.get("/notifications/");
  return data;
}

export async function markNotificationRead(notificationId: number) {
  const { data } = await http.post(`/notifications/${notificationId}/read/`);
  return data;
}

export async function markAllNotificationsRead() {
  const { data } = await http.post("/notifications/read-all/");
  return data;
}
