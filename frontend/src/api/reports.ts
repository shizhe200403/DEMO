import http from "./http";

export async function getReportDashboard() {
  const { data } = await http.get("/reports/dashboard/");
  return data;
}

export async function weeklyReport() {
  const { data } = await http.get("/reports/weekly/");
  return data;
}

export async function monthlyReport() {
  const { data } = await http.get("/reports/monthly/");
  return data;
}

export async function listReportTasks() {
  const { data } = await http.get("/reports/tasks/");
  return data;
}

export async function getReportTask(taskId: string) {
  const { data } = await http.get(`/reports/tasks/${taskId}/`);
  return data;
}

export async function deleteReportTask(taskId: string) {
  const { data } = await http.delete(`/reports/tasks/${taskId}/`);
  return data;
}

export async function exportReport(payload: Record<string, unknown>) {
  const { data } = await http.post("/reports/export/", payload);
  return data;
}
