import http from "./http";

export async function listRecipes() {
  const { data } = await http.get("/recipes/");
  return data;
}

export async function listRecommendations() {
  const { data } = await http.get("/recommendations/home/");
  return data;
}

export async function explainRecommendation(recipeId: number) {
  const { data } = await http.get(`/recommendations/explain/${recipeId}/`);
  return data;
}
