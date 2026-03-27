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
