import http from "./http";

export async function listRecipes() {
  const { data } = await http.get("/recipes/");
  return data;
}

export async function getRecipeDetail(recipeId: number) {
  const { data } = await http.get(`/recipes/${recipeId}/`);
  return data;
}

export async function listFavoriteRecipes() {
  const { data } = await http.get("/recipes/favorites/");
  return data;
}

export async function getRecipeNutrition(recipeId: number) {
  const { data } = await http.get(`/recipes/${recipeId}/nutrition/`);
  return data;
}

export async function favoriteRecipe(recipeId: number) {
  const { data } = await http.post(`/recipes/${recipeId}/favorite/`);
  return data;
}

export async function unfavoriteRecipe(recipeId: number) {
  const { data } = await http.delete(`/recipes/${recipeId}/favorite/`);
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

export async function createRecipe(payload: Record<string, unknown>) {
  const { data } = await http.post("/recipes/", payload);
  return data;
}

export async function updateRecipe(recipeId: number, payload: Record<string, unknown>) {
  const { data } = await http.patch(`/recipes/${recipeId}/`, payload);
  return data;
}

export async function bulkUpdateRecipes(payload: { ids: number[]; action: "approve" | "reject" | "archive" }) {
  const { data } = await http.post("/recipes/admin/bulk/", payload);
  return data;
}

export async function deleteRecipe(recipeId: number) {
  const { data } = await http.delete(`/recipes/${recipeId}/`);
  return data;
}

export async function uploadRecipeCover(recipeId: number, file: File) {
  const form = new FormData();
  form.append("cover", file);
  const { data } = await http.post(`/recipes/${recipeId}/upload_cover/`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listIngredients() {
  const { data } = await http.get("/ingredients/");
  return data;
}

export async function profileRecommendations() {
  const { data } = await http.get("/recommendations/by-profile/");
  return data;
}
