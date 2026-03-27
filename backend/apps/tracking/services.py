from decimal import Decimal

from django.db.models import F, Sum

from .models import MealRecordItem


def build_meal_statistics(user, start_date, end_date):
    queryset = (
        MealRecordItem.objects.filter(meal_record__user=user, meal_record__record_date__range=(start_date, end_date))
        .annotate(day=F("meal_record__record_date"))
        .values("day")
        .annotate(
            total_energy=Sum("energy"),
            total_protein=Sum("protein"),
            total_fat=Sum("fat"),
            total_carbohydrate=Sum("carbohydrate"),
        )
        .order_by("day")
    )

    days = []
    for row in queryset:
        days.append(
            {
                "date": row["day"],
                "energy": row["total_energy"] or Decimal("0"),
                "protein": row["total_protein"] or Decimal("0"),
                "fat": row["total_fat"] or Decimal("0"),
                "carbohydrate": row["total_carbohydrate"] or Decimal("0"),
            }
        )

    return days


def build_meal_summary(user, start_date, end_date):
    queryset = MealRecordItem.objects.filter(meal_record__user=user, meal_record__record_date__range=(start_date, end_date))
    total = queryset.aggregate(
        total_energy=Sum("energy"),
        total_protein=Sum("protein"),
        total_fat=Sum("fat"),
        total_carbohydrate=Sum("carbohydrate"),
    )
    return {
        "energy": total["total_energy"] or Decimal("0"),
        "protein": total["total_protein"] or Decimal("0"),
        "fat": total["total_fat"] or Decimal("0"),
        "carbohydrate": total["total_carbohydrate"] or Decimal("0"),
    }
