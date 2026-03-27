import http from "./http";

export async function listMealRecords() {
  const { data } = await http.get("/meal-records/");
  return data;
}

export async function createMealRecord(payload: Record<string, unknown>) {
  const { data } = await http.post("/meal-records/", payload);
  return data;
}

export async function mealStatistics(period = "week") {
  const { data } = await http.get("/meal-records/statistics/", { params: { period } });
  return data;
}
