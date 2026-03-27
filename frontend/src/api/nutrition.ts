import http from "./http";

export async function nutritionAnalysis() {
  const { data } = await http.get("/nutrition/analysis/");
  return data;
}

export async function calculateRecipeNutrition(payload: Record<string, unknown>) {
  const { data } = await http.post("/nutrition/calculate/", payload);
  return data;
}

