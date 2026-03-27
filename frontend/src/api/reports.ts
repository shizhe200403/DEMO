import http from "./http";

export async function weeklyReport() {
  const { data } = await http.get("/reports/weekly/");
  return data;
}

export async function monthlyReport() {
  const { data } = await http.get("/reports/monthly/");
  return data;
}

export async function exportReport(payload: Record<string, unknown>) {
  const { data } = await http.post("/reports/export/", payload);
  return data;
}

