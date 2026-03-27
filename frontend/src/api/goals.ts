import http from "./http";

export async function listHealthGoals() {
  const { data } = await http.get("/health-goals/");
  return data;
}

export async function createHealthGoal(payload: Record<string, unknown>) {
  const { data } = await http.post("/health-goals/", payload);
  return data;
}

export async function updateHealthGoal(goalId: number, payload: Record<string, unknown>) {
  const { data } = await http.patch(`/health-goals/${goalId}/`, payload);
  return data;
}

export async function listGoalProgress(goalId: number) {
  const { data } = await http.get(`/health-goals/${goalId}/progress/`);
  return data;
}

export async function createGoalProgress(goalId: number, payload: Record<string, unknown>) {
  const { data } = await http.post(`/health-goals/${goalId}/progress/`, payload);
  return data;
}
