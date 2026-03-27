import os
from typing import Any

import requests
from django.core.cache import cache


def _get_json(url: str, headers=None, params=None, cache_key: str | None = None, timeout: int = 10):
    if cache_key:
        try:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        except Exception:
            pass

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    if cache_key:
        try:
            cache.set(cache_key, data, timeout=3600)
        except Exception:
            pass
    return data


def search_usda(query: str) -> dict[str, Any]:
    api_key = os.getenv("EXTERNAL_USDA_API_KEY")
    if not api_key:
        return {"items": [], "source": "usda", "degraded": True}
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    data = _get_json(
        url,
        params={"query": query, "api_key": api_key, "pageSize": 10},
        cache_key=f"usda:{query}",
    )
    if data is None:
        return {"items": [], "source": "usda", "degraded": True}
    return {"items": data.get("foods", []), "source": "usda", "degraded": False}


def search_nutritionix(query: str) -> dict[str, Any]:
    app_id = os.getenv("EXTERNAL_NUTRITIONIX_APP_ID")
    api_key = os.getenv("EXTERNAL_NUTRITIONIX_API_KEY")
    if not app_id or not api_key:
        return {"items": [], "source": "nutritionix", "degraded": True}
    url = "https://trackapi.nutritionix.com/v2/search/instant"
    data = _get_json(
        url,
        headers={"x-app-id": app_id, "x-app-key": api_key},
        params={"query": query},
        cache_key=f"nutritionix:{query}",
    )
    if data is None:
        return {"items": [], "source": "nutritionix", "degraded": True}
    return {"items": data, "source": "nutritionix", "degraded": False}


def search_edamam_recipes(query: str) -> dict[str, Any]:
    app_id = os.getenv("EXTERNAL_EDAMAM_APP_ID")
    api_key = os.getenv("EXTERNAL_EDAMAM_APP_KEY")
    if not app_id or not api_key:
        return {"items": [], "source": "edamam", "degraded": True}
    url = "https://api.edamam.com/search"
    data = _get_json(
        url,
        params={"q": query, "app_id": app_id, "app_key": api_key, "to": 10},
        cache_key=f"edamam:{query}",
    )
    if data is None:
        return {"items": [], "source": "edamam", "degraded": True}
    return {"items": data.get("hits", []), "source": "edamam", "degraded": False}


def lookup_openfoodfacts_barcode(code: str) -> dict[str, Any]:
    url = f"https://world.openfoodfacts.org/api/v2/product/{code}.json"
    data = _get_json(url, cache_key=f"openfoodfacts:{code}")
    if data is None:
        return {"items": {}, "source": "openfoodfacts", "degraded": True}
    return {"items": data, "source": "openfoodfacts", "degraded": False}
