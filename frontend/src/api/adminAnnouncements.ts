import http from "./http";

export interface AdminAnnouncementItem {
  id: number;
  title: string;
  body: string;
  link_path: string;
  notification_count: number;
  published_at: string;
  created_by?: {
    id: number | null;
    username: string;
    nickname: string;
    display_name: string;
  } | null;
}

export async function listAdminAnnouncements() {
  const { data } = await http.get("/admin/announcements/");
  return data as { data?: { items?: AdminAnnouncementItem[] } };
}

export async function createAdminAnnouncement(payload: Record<string, unknown>) {
  const { data } = await http.post("/admin/announcements/", payload);
  return data as { data?: { items?: AdminAnnouncementItem[] } };
}
