import http from "./http";

export type ExternalFoodItem = {
  id: string;
  title: string;
  subtitle: string;
  source: "nutritionix" | "usda" | "openfoodfacts" | "edamam";
  unit: string;
  energy: number;
  protein: number;
  fat: number;
  carbohydrate: number;
};

export type ExternalRecipeIdea = {
  id: string;
  title: string;
  source: "edamam";
  url: string;
  image: string;
  mealType: string;
  cookTimeMinutes: number;
  servings: number;
  energy: number;
  protein: number;
  fat: number;
  carbohydrate: number;
  ingredientLines: string[];
};

function unwrapPayload<T>(payload: unknown, fallback: T): T {
  if (payload == null) {
    return fallback;
  }
  if (typeof payload === "object" && payload && "data" in payload && (payload as { data?: T }).data !== undefined) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

function numericValue(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function roundMetric(value: unknown) {
  const number = numericValue(value);
  return Math.round(number * 10) / 10;
}

function nutrientFromUsda(food: Record<string, any>, nutrientNames: string[], nutrientNumbers: number[]) {
  const nutrients = Array.isArray(food.foodNutrients) ? food.foodNutrients : [];
  const hit = nutrients.find((item: Record<string, any>) => {
    const name = String(item.nutrientName || item.name || "").toLowerCase();
    const number = Number(item.nutrientNumber || item.number || 0);
    return nutrientNames.some((candidate) => name.includes(candidate)) || nutrientNumbers.includes(number);
  });
  return numericValue(hit?.value);
}

function mapNutritionixFoods(items: Record<string, any>[]) {
  return items.map((food: Record<string, any>, index: number) => ({
    id: `nutritionix-${food.tag_id || food.nix_item_id || `${food.food_name || "item"}-${index}`}`,
    title: String(food.food_name || food.food_name_original || "未命名食物"),
    subtitle: [food.brand_name, food.serving_weight_grams ? `${roundMetric(food.serving_weight_grams)}g` : ""]
      .filter(Boolean)
      .join(" · ") || "Nutritionix 食物数据",
    source: "nutritionix" as const,
    unit: [food.serving_qty, food.serving_unit].filter(Boolean).join(" ") || "1 serving",
    energy: roundMetric(food.nf_calories),
    protein: roundMetric(food.nf_protein),
    fat: roundMetric(food.nf_total_fat),
    carbohydrate: roundMetric(food.nf_total_carbohydrate),
  }));
}

function mapUsdaFoods(items: Record<string, any>[]) {
  return items.map((food: Record<string, any>, index: number) => ({
    id: `usda-${food.fdcId || index}`,
    title: String(food.description || "未命名食物"),
    subtitle: [food.brandOwner, food.dataType].filter(Boolean).join(" · ") || "USDA 食物数据",
    source: "usda" as const,
    unit: food.servingSizeUnit ? `${food.servingSize || 100}${food.servingSizeUnit}` : "100g",
    energy: roundMetric(nutrientFromUsda(food, ["energy"], [208])),
    protein: roundMetric(nutrientFromUsda(food, ["protein"], [203])),
    fat: roundMetric(nutrientFromUsda(food, ["total lipid", "fat"], [204])),
    carbohydrate: roundMetric(nutrientFromUsda(food, ["carbohydrate"], [205])),
  }));
}

export async function searchExternalFoods(query: string) {
  try {
    const response = await http.get("/external/nutritionix/search/", { params: { q: query } });
    const payload = unwrapPayload<Record<string, any>>(response.data, {});
    const items = Array.isArray(payload?.items) ? payload.items : [];
    const mappedItems = mapNutritionixFoods(items).filter((item) => item.energy > 0 || item.protein > 0 || item.fat > 0 || item.carbohydrate > 0);

    if (mappedItems.length) {
      return {
        degraded: Boolean(payload?.degraded),
        items: mappedItems,
      };
    }
  } catch {
    // Fallback to USDA when Nutritionix is unavailable or not configured.
  }

  const fallbackResponse = await http.get("/external/usda/search/", { params: { q: query } });
  const fallbackPayload = unwrapPayload<Record<string, any>>(fallbackResponse.data, {});
  const fallbackItems = Array.isArray(fallbackPayload?.items) ? fallbackPayload.items : [];

  return {
    degraded: Boolean(fallbackPayload?.degraded),
    items: mapUsdaFoods(fallbackItems),
  };
}

export async function lookupBarcodeFood(code: string) {
  const response = await http.get(`/external/openfoodfacts/barcode/${code}/`);
  const payload = unwrapPayload<Record<string, any>>(response.data, {});
  const product = payload?.items?.product;
  const nutriments = product?.nutriments ?? {};

  if (!product) {
    return { degraded: Boolean(payload?.degraded), item: null as ExternalFoodItem | null };
  }

  return {
    degraded: Boolean(payload?.degraded),
    item: {
      id: `openfoodfacts-${code}`,
      title: String(product.product_name || product.generic_name || code),
      subtitle: [product.brands, product.quantity].filter(Boolean).join(" · ") || "OpenFoodFacts 商品数据",
      source: "openfoodfacts" as const,
      unit: "100g",
      energy: roundMetric(nutriments["energy-kcal_100g"] ?? nutriments.energy_kcal_100g),
      protein: roundMetric(nutriments.proteins_100g),
      fat: roundMetric(nutriments.fat_100g),
      carbohydrate: roundMetric(nutriments.carbohydrates_100g),
    },
  };
}

export async function searchExternalRecipeIdeas(query: string) {
  const response = await http.get("/external/edamam/recipes/", { params: { q: query } });
  const payload = unwrapPayload<Record<string, any>>(response.data, {});
  const hits = Array.isArray(payload?.items) ? payload.items : [];

  return {
    degraded: Boolean(payload?.degraded),
    items: hits.map((entry: Record<string, any>, index: number) => {
      const recipe = entry.recipe ?? {};
      const servings = Math.max(1, numericValue(recipe.yield || 1));
      return {
        id: `edamam-${index}-${String(recipe.uri || recipe.label || "").slice(-12)}`,
        title: String(recipe.label || "外部菜谱"),
        source: "edamam" as const,
        url: String(recipe.url || ""),
        image: String(recipe.image || ""),
        mealType: Array.isArray(recipe.mealType) ? String(recipe.mealType[0] || "") : String(recipe.mealType || ""),
        cookTimeMinutes: numericValue(recipe.totalTime),
        servings,
        energy: roundMetric(numericValue(recipe.calories) / servings),
        protein: roundMetric(numericValue(recipe.totalNutrients?.PROCNT?.quantity) / servings),
        fat: roundMetric(numericValue(recipe.totalNutrients?.FAT?.quantity) / servings),
        carbohydrate: roundMetric(numericValue(recipe.totalNutrients?.CHOCDF?.quantity) / servings),
        ingredientLines: Array.isArray(recipe.ingredientLines) ? recipe.ingredientLines : [],
      };
    }),
  };
}
