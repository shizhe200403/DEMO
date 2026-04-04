import http from "./http";

export async function listMealRecords() {
  const { data } = await http.get("/meal-records/");
  return data;
}

export async function createMealRecord(payload: Record<string, unknown>) {
  const { data } = await http.post("/meal-records/", payload);
  return data;
}

export async function deleteMealRecord(recordId: number) {
  const { data } = await http.delete(`/meal-records/${recordId}/`);
  return data;
}

export async function updateMealRecord(recordId: number, payload: Record<string, unknown>) {
  const { data } = await http.put(`/meal-records/${recordId}/`, payload);
  return data;
}

export async function mealStatistics(period = "week") {
  const { data } = await http.get("/meal-records/statistics/", { params: { period } });
  return data;
}

export async function copyYesterdayMealRecords() {
  const { data } = await http.post("/meal-records/copy-yesterday/");
  return data;
}
