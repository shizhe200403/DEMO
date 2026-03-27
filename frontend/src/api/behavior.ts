import http from "./http";

export async function trackEvent(payload: Record<string, unknown>) {
  const { data } = await http.post("/events/track/", payload);
  return data;
}

