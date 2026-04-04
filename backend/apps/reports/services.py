from datetime import timedelta
from pathlib import Path
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from apps.nutrition.services import analyze_user_nutrition
from apps.tracking.models import HealthGoal, MealRecord
from apps.tracking.services import build_meal_statistics, build_meal_summary

from .models import ReportTask


def report_period(report_type: str):
    end_date = timezone.localdate()
    if report_type == "monthly":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)
    return start_date, end_date


def generate_pdf_report(user, report_type: str, start_date, end_date):
    summary = build_meal_summary(user, start_date, end_date)
    trend = build_meal_statistics(user, start_date, end_date)
    nutrition = analyze_user_nutrition(user)
    goals = list(
        HealthGoal.objects.filter(user=user, status__in=["active", "completed"])
        .order_by("-created_at")[:6]
    )

    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    reports_dir = Path(settings.MEDIA_ROOT) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{user.id}_{report_type}_{start_date}_{end_date}_{ts}.pdf"
    file_path = reports_dir / file_name

    W, H = A4
    pdf = canvas.Canvas(str(file_path), pagesize=A4)

    # ── 辅助函数 ────────────────────────────────────────────
    def check_page(current_y, need=40):
        if current_y < need + 50:
            pdf.showPage()
            _draw_header_line()
            return H - 70
        return current_y

    def _draw_header_line():
        pdf.setFont("STSong-Light", 8)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawString(50, H - 30, f"营养健康报告  |  {user.username}  |  {start_date} — {end_date}")
        pdf.setFillColorRGB(0, 0, 0)
        pdf.line(50, H - 35, W - 50, H - 35)

    def section_title(y, text):
        y = check_page(y, 40)
        y -= 10
        pdf.setFont("STSong-Light", 13)
        pdf.setFillColorRGB(0.12, 0.37, 0.62)
        pdf.drawString(50, y, text)
        pdf.setFillColorRGB(0, 0, 0)
        pdf.line(50, y - 4, W - 50, y - 4)
        return y - 20

    def row(y, label, value, indent=50):
        y = check_page(y)
        pdf.setFont("STSong-Light", 10)
        pdf.drawString(indent, y, f"{label}")
        pdf.drawRightString(W - 50, y, f"{value}")
        pdf.setFillColorRGB(0.85, 0.85, 0.85)
        pdf.line(indent + 120, y + 3, W - 50, y + 3)
        pdf.setFillColorRGB(0, 0, 0)
        return y - 16

    def pct(actual, target):
        if not target or target == 0:
            return "—"
        r = float(Decimal(str(actual)) / Decimal(str(target)) * 100)
        return f"{r:.1f}%"

    def q(val, digits=1):
        if val is None:
            return "—"
        try:
            return str(Decimal(str(val)).quantize(Decimal(f"1.{'0'*digits}")))
        except Exception:
            return str(val)

    # ── 封面 ──────────────────────────────────────────────
    pdf.setFont("STSong-Light", 22)
    pdf.setFillColorRGB(0.12, 0.37, 0.62)
    pdf.drawCentredString(W / 2, H - 130, "营养健康报告")
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("STSong-Light", 12)
    report_type_label = "周报（近7天）" if report_type == "weekly" else "月报（近30天）"
    pdf.drawCentredString(W / 2, H - 165, report_type_label)
    pdf.drawCentredString(W / 2, H - 185, f"统计周期：{start_date}  至  {end_date}")
    pdf.drawCentredString(W / 2, H - 205, f"用户：{user.username}")
    pdf.setFont("STSong-Light", 9)
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.drawCentredString(W / 2, H - 230, f"生成时间：{timezone.localdate()}")
    pdf.setFillColorRGB(0, 0, 0)
    pdf.line(50, H - 245, W - 50, H - 245)

    # 封面健康快览
    y = H - 290
    bmi_val = nutrition.get("bmi")
    calorie_target = nutrition.get("calorie_target")
    protein_target = nutrition.get("protein_target")
    fat_target = nutrition.get("fat_target")
    carb_target = nutrition.get("carb_target")
    balance_score = nutrition.get("balance_score")
    adequacy = nutrition.get("adequacy") or {}

    pdf.setFont("STSong-Light", 11)
    def cover_kv(label, val, unit=""):
        nonlocal y
        pdf.drawString(80, y, f"  {label}")
        pdf.setFont("STSong-Light", 13)
        pdf.drawString(220, y, f"{val}{unit}")
        pdf.setFont("STSong-Light", 11)
        y -= 22

    if bmi_val:
        bmi_f = float(Decimal(str(bmi_val)).quantize(Decimal("0.1")))
        if bmi_f < 18.5:
            bmi_label = "偏瘦"
        elif bmi_f < 24:
            bmi_label = "正常"
        elif bmi_f < 28:
            bmi_label = "偏胖"
        else:
            bmi_label = "肥胖"
        cover_kv("BMI", f"{bmi_f:.1f}  ({bmi_label})")
    if calorie_target:
        cover_kv("每日热量目标", q(calorie_target, 0), " kcal")
    if protein_target:
        cover_kv("每日蛋白质目标", q(protein_target), " g")
    if balance_score is not None:
        cover_kv("膳食均衡评分", f"{balance_score} / 100")
    cover_kv("健康目标建议", nutrition.get("goal_hint", "—"))

    pdf.showPage()

    # ── 第2页起正文 ────────────────────────────────────────
    _draw_header_line()
    y = H - 70

    # 1. 摄入总览
    days = (end_date - start_date).days + 1
    y = section_title(y, "一、营养摄入总览")
    y = row(y, f"统计天数", f"{days} 天")
    y = row(y, "有记录天数", f"{adequacy.get('days_recorded', '—')} 天")
    y = row(y, "总热量摄入", f"{q(summary['energy'], 1)} kcal")
    y = row(y, "总蛋白质", f"{q(summary['protein'], 1)} g")
    y = row(y, "总脂肪", f"{q(summary['fat'], 1)} g")
    y = row(y, "总碳水化合物", f"{q(summary['carbohydrate'], 1)} g")
    if days > 0:
        def avg(val):
            try:
                return q(Decimal(str(val)) / Decimal(str(days)), 1)
            except Exception:
                return "—"
        y -= 4
        y = row(y, "日均热量", f"{avg(summary['energy'])} kcal")
        y = row(y, "日均蛋白质", f"{avg(summary['protein'])} g")
        y = row(y, "日均脂肪", f"{avg(summary['fat'])} g")
        y = row(y, "日均碳水", f"{avg(summary['carbohydrate'])} g")

    # 2. 营养目标对比
    y = section_title(y, "二、营养目标对比（DRIs 参照）")
    headers = [("指标", 50), ("目标值", 200), ("近7天日均", 310), ("达标率", 430)]
    y = check_page(y, 30)
    pdf.setFont("STSong-Light", 10)
    pdf.setFillColorRGB(0.2, 0.2, 0.2)
    for label, x in headers:
        pdf.drawString(x, y, label)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.line(50, y - 4, W - 50, y - 4)
    y -= 18

    def target_row(label, target, actual_key, unit):
        nonlocal y
        y = check_page(y)
        actual = adequacy.get(actual_key)
        pdf.setFont("STSong-Light", 10)
        pdf.drawString(50, y, label)
        pdf.drawString(200, y, f"{q(target)} {unit}" if target else "—")
        pdf.drawString(310, y, f"{actual:.1f} {unit}" if actual is not None else "—")
        pdf.drawString(430, y, pct(actual, target) if actual is not None else "—")
        y -= 16

    target_row("热量", calorie_target, "avg_energy", "kcal")
    target_row("蛋白质", protein_target, "avg_protein", "g")
    target_row("脂肪", fat_target, "avg_fat", "g")
    target_row("碳水化合物", carb_target, "avg_carb", "g")
    y -= 4
    pdf.setFont("STSong-Light", 9)
    pdf.setFillColorRGB(0.4, 0.4, 0.4)
    pdf.drawString(50, y, "* 膳食纤维目标：" + q(nutrition.get("fiber_target")) + " g/天    "
                   "钠限量：" + q(nutrition.get("sodium_limit")) + " mg/天    "
                   "钙：" + q(nutrition.get("calcium_target")) + " mg/天    "
                   "铁：" + q(nutrition.get("iron_target")) + " mg/天    "
                   "VC：" + q(nutrition.get("vitamin_c_target")) + " mg/天")
    pdf.setFillColorRGB(0, 0, 0)
    y -= 20

    # 3. 膳食均衡评估
    y = section_title(y, "三、膳食均衡评估")
    if balance_score is not None:
        if balance_score >= 80:
            grade, advice = "优秀", "各营养素摄入较为均衡，请继续保持。"
        elif balance_score >= 60:
            grade, advice = "良好", "整体均衡，部分营养素可进一步优化。"
        elif balance_score >= 40:
            grade, advice = "一般", "存在明显缺口或过量，建议调整饮食结构。"
        else:
            grade, advice = "较差", "营养摄入严重失衡，建议咨询营养师。"
        y = check_page(y)
        pdf.setFont("STSong-Light", 11)
        pdf.drawString(50, y, f"综合评分：{balance_score} 分  ({grade})")
        y -= 18
        pdf.setFont("STSong-Light", 10)
        pdf.drawString(50, y, f"建议：{advice}")
        y -= 18
        pdf.drawString(50, y, f"健康提示：{nutrition.get('goal_hint', '—')}")
        y -= 12
    else:
        y = check_page(y)
        pdf.setFont("STSong-Light", 10)
        pdf.drawString(50, y, "暂无足够饮食记录，无法计算均衡评分。建议坚持记录饮食以获取个性化评估。")
        y -= 18

    # 4. 健康目标完成情况
    if goals:
        y = section_title(y, "四、健康目标完成情况")
        goal_label_map = {
            "weight_loss": "减重", "muscle_gain": "增肌", "blood_sugar_control": "控糖",
            "fat_control": "控脂", "protein_up": "增蛋白", "diet_balance": "饮食均衡",
        }
        status_map = {"active": "进行中", "completed": "已完成", "paused": "已暂停", "cancelled": "已取消"}
        for goal in goals:
            y = check_page(y, 50)
            label = goal_label_map.get(goal.goal_type, goal.goal_type)
            current = goal.current_value or Decimal("0")
            target = goal.target_value or Decimal("0")
            progress_pct = pct(current, target) if target else "—"
            pdf.setFont("STSong-Light", 10)
            pdf.drawString(50, y, f"▸ {label}：{q(current)} / {q(target)}   完成率 {progress_pct}   [{status_map.get(goal.status, goal.status)}]")
            y -= 14
            if goal.description:
                pdf.setFont("STSong-Light", 9)
                pdf.setFillColorRGB(0.4, 0.4, 0.4)
                pdf.drawString(62, y, goal.description[:60])
                pdf.setFillColorRGB(0, 0, 0)
                y -= 14

    # 5. 每日营养趋势
    y = section_title(y, "五、每日营养趋势")
    y = check_page(y, 30)
    col_x = [50, 130, 240, 330, 420]
    headers2 = ["日期", "热量(kcal)", "蛋白质(g)", "脂肪(g)", "碳水(g)"]
    pdf.setFont("STSong-Light", 9)
    pdf.setFillColorRGB(0.2, 0.2, 0.2)
    for x, h in zip(col_x, headers2):
        pdf.drawString(x, y, h)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.line(50, y - 3, W - 50, y - 3)
    y -= 15
    for i, day_row in enumerate(trend):
        y = check_page(y)
        pdf.setFont("STSong-Light", 9)
        if i % 2 == 0:
            pdf.setFillColorRGB(0.95, 0.95, 0.95)
            pdf.rect(48, y - 2, W - 96, 13, fill=1, stroke=0)
            pdf.setFillColorRGB(0, 0, 0)
        pdf.drawString(col_x[0], y, str(day_row["date"]))
        pdf.drawString(col_x[1], y, q(day_row["energy"], 0))
        pdf.drawString(col_x[2], y, q(day_row["protein"], 1))
        pdf.drawString(col_x[3], y, q(day_row["fat"], 1))
        pdf.drawString(col_x[4], y, q(day_row["carbohydrate"], 1))
        y -= 13

    # 页脚
    pdf.setFont("STSong-Light", 8)
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.drawCentredString(W / 2, 30, "本报告由智能菜谱推荐与营养健康管理系统自动生成，数据仅供参考，不构成医疗建议。")
    pdf.setFillColorRGB(0, 0, 0)

    pdf.save()
    return file_path


def _quantize(value, digits="0.1"):
    if value in (None, ""):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value.quantize(Decimal(digits))
    return Decimal(str(value)).quantize(Decimal(digits))


def _to_number(value, digits=1):
    if value in (None, ""):
        return 0
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    quantized = value.quantize(Decimal("1") if digits == 0 else Decimal(f"1.{'0' * digits}"))
    number = float(quantized)
    if digits == 0:
        return int(number)
    return number


def _ratio(value, total):
    if not total:
        return 0
    return max(0, min(100, round(float(value) / float(total) * 100)))


def _safe_progress(current, target):
    if not target:
        return 0
    return max(0, min(100, round(float(current) / float(target) * 100)))


def _format_short_date(value):
    return value.strftime("%m/%d")


def _format_weekday(value):
    return ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][value.weekday()]


def build_report_dashboard(user):
    today = timezone.localdate()
    start_month = today - timedelta(days=29)
    start_fortnight = today - timedelta(days=13)
    start_week = today - timedelta(days=6)

    records = list(
        MealRecord.objects.filter(user=user, record_date__range=(start_month, today))
        .prefetch_related("items", "items__recipe")
        .order_by("record_date", "created_at")
    )
    goals = list(
        HealthGoal.objects.filter(user=user, status="active")
        .prefetch_related("progress_records")
        .order_by("-updated_at", "-id")
    )
    report_tasks = list(ReportTask.objects.filter(user=user).order_by("-created_at")[:20])
    nutrition_targets = analyze_user_nutrition(user)

    day_rows = {}
    meal_distribution = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    macro_totals_14 = {"protein": Decimal("0"), "fat": Decimal("0"), "carbohydrate": Decimal("0")}
    weekday_map = {
        "周一": {"energy": Decimal("0"), "protein": Decimal("0"), "meals": 0, "active_days": 0},
        "周二": {"energy": Decimal("0"), "protein": Decimal("0"), "meals": 0, "active_days": 0},
        "周三": {"energy": Decimal("0"), "protein": Decimal("0"), "meals": 0, "active_days": 0},
        "周四": {"energy": Decimal("0"), "protein": Decimal("0"), "meals": 0, "active_days": 0},
        "周五": {"energy": Decimal("0"), "protein": Decimal("0"), "meals": 0, "active_days": 0},
        "周六": {"energy": Decimal("0"), "protein": Decimal("0"), "meals": 0, "active_days": 0},
        "周日": {"energy": Decimal("0"), "protein": Decimal("0"), "meals": 0, "active_days": 0},
    }
    meal_completion = {"breakfast": set(), "lunch": set(), "dinner": set(), "snack": set()}

    for offset in range(30):
        current = start_month + timedelta(days=offset)
        day_rows[current] = {
            "date": current,
            "label": _format_short_date(current),
            "weekday": _format_weekday(current),
            "energy": Decimal("0"),
            "protein": Decimal("0"),
            "fat": Decimal("0"),
            "carbohydrate": Decimal("0"),
            "meals": 0,
            "recipe_linked_meals": 0,
            "meal_types": set(),
        }

    for record in records:
        day_row = day_rows[record.record_date]
        energy = Decimal("0")
        protein = Decimal("0")
        fat = Decimal("0")
        carbohydrate = Decimal("0")
        recipe_linked = False

        for item in record.items.all():
            energy += item.energy or Decimal("0")
            protein += item.protein or Decimal("0")
            fat += item.fat or Decimal("0")
            carbohydrate += item.carbohydrate or Decimal("0")
            recipe_linked = recipe_linked or bool(item.recipe_id)

        day_row["energy"] += energy
        day_row["protein"] += protein
        day_row["fat"] += fat
        day_row["carbohydrate"] += carbohydrate
        day_row["meals"] += 1
        day_row["meal_types"].add(record.meal_type)
        if recipe_linked:
            day_row["recipe_linked_meals"] += 1

        meal_distribution[record.meal_type] = meal_distribution.get(record.meal_type, 0) + 1
        meal_completion.setdefault(record.meal_type, set()).add(record.record_date)

        if record.record_date >= start_fortnight:
            macro_totals_14["protein"] += protein
            macro_totals_14["fat"] += fat
            macro_totals_14["carbohydrate"] += carbohydrate
            weekday_row = weekday_map[day_row["weekday"]]
            weekday_row["energy"] += energy
            weekday_row["protein"] += protein
            weekday_row["meals"] += 1

    for row in day_rows.values():
        if row["meals"] > 0:
            weekday_map[row["weekday"]]["active_days"] += 1

    def period_summary(start_date):
        rows = [row for date_key, row in day_rows.items() if date_key >= start_date]
        total_energy = sum((row["energy"] for row in rows), Decimal("0"))
        total_protein = sum((row["protein"] for row in rows), Decimal("0"))
        total_fat = sum((row["fat"] for row in rows), Decimal("0"))
        total_carb = sum((row["carbohydrate"] for row in rows), Decimal("0"))
        total_meals = sum(row["meals"] for row in rows)
        active_days = sum(1 for row in rows if row["meals"] > 0)
        recipe_linked_meals = sum(row["recipe_linked_meals"] for row in rows)
        average_active_energy = total_energy / active_days if active_days else Decimal("0")
        average_active_protein = total_protein / active_days if active_days else Decimal("0")
        average_active_fat = total_fat / active_days if active_days else Decimal("0")
        average_active_carb = total_carb / active_days if active_days else Decimal("0")
        return {
            "start_date": str(start_date),
            "end_date": str(today),
            "active_days": active_days,
            "meals": total_meals,
            "recipe_linked_meals": recipe_linked_meals,
            "recipe_link_rate": _ratio(recipe_linked_meals, total_meals),
            "totals": {
                "energy": _to_number(total_energy, 0),
                "protein": _to_number(total_protein),
                "fat": _to_number(total_fat),
                "carbohydrate": _to_number(total_carb),
            },
            "averages": {
                "energy": _to_number(average_active_energy, 0),
                "protein": _to_number(average_active_protein),
                "fat": _to_number(average_active_fat),
                "carbohydrate": _to_number(average_active_carb),
            },
        }

    week = period_summary(start_week)
    fortnight = period_summary(start_fortnight)
    month = period_summary(start_month)
    calorie_target = nutrition_targets.get("calorie_target")
    protein_target = nutrition_targets.get("protein_target")

    latest_completed = next((task for task in report_tasks if task.status == "completed"), None)
    report_assets = {
        "total": len(report_tasks),
        "completed": sum(1 for task in report_tasks if task.status == "completed"),
        "processing": sum(1 for task in report_tasks if task.status in {"pending", "processing"}),
        "failed": sum(1 for task in report_tasks if task.status == "failed"),
        "latest_generated_at": latest_completed.generated_at.isoformat() if latest_completed and latest_completed.generated_at else "",
        "latest_completed_report_type": latest_completed.report_type if latest_completed else "",
        "latest_completed_file_url": latest_completed.file_url if latest_completed else "",
    }

    headline_cards = [
        {
            "key": "daily_energy",
            "label": "近7天日均热量",
            "value": week["averages"]["energy"],
            "unit": "kcal",
            "target": _to_number(calorie_target, 0),
            "progress": _safe_progress(week["averages"]["energy"], calorie_target or 0),
            "tone": "warm",
            "caption": "和当前估算能量目标相比",
        },
        {
            "key": "daily_protein",
            "label": "近7天日均蛋白",
            "value": week["averages"]["protein"],
            "unit": "g",
            "target": _to_number(protein_target),
            "progress": _safe_progress(week["averages"]["protein"], protein_target or 0),
            "tone": "primary",
            "caption": "按活跃天估算的蛋白完成度",
        },
        {
            "key": "active_days",
            "label": "近7天活跃天数",
            "value": week["active_days"],
            "unit": "天",
            "target": 7,
            "progress": _safe_progress(week["active_days"], 7),
            "tone": "success",
            "caption": "越连续，复盘越真实",
        },
        {
            "key": "report_assets",
            "label": "已沉淀报表",
            "value": report_assets["completed"],
            "unit": "份",
            "target": max(report_assets["completed"], 4) or 4,
            "progress": _safe_progress(report_assets["completed"], max(report_assets["completed"], 4) or 4),
            "tone": "accent",
            "caption": "可回看的历史报表资产",
        },
    ]

    trend_rows = []
    for row in [value for key, value in day_rows.items() if key >= start_fortnight]:
        trend_rows.append(
            {
                "date": str(row["date"]),
                "label": row["label"],
                "weekday": row["weekday"],
                "energy": _to_number(row["energy"], 0),
                "protein": _to_number(row["protein"]),
                "fat": _to_number(row["fat"]),
                "carbohydrate": _to_number(row["carbohydrate"]),
                "meals": row["meals"],
                "recipe_linked_meals": row["recipe_linked_meals"],
            }
        )

    total_macros = sum(macro_totals_14.values(), Decimal("0"))
    macro_colors = {
        "protein": "#3c7dff",
        "fat": "#ff8a1c",
        "carbohydrate": "#9d5cff",
    }
    macro_labels = {
        "protein": "蛋白质",
        "fat": "脂肪",
        "carbohydrate": "碳水",
    }
    macro_distribution = [
        {
            "key": key,
            "label": macro_labels[key],
            "value": _to_number(value),
            "percentage": _ratio(value, total_macros),
            "color": macro_colors[key],
        }
        for key, value in macro_totals_14.items()
    ]

    meal_colors = {
        "breakfast": "#5c8dff",
        "lunch": "#ff7e1b",
        "dinner": "#9f58ff",
        "snack": "#31c96d",
    }
    meal_labels = {
        "breakfast": "早餐",
        "lunch": "午餐",
        "dinner": "晚餐",
        "snack": "加餐",
    }
    total_meal_distribution = sum(meal_distribution.values())
    meal_distribution_items = [
        {
            "key": key,
            "label": meal_labels[key],
            "value": meal_distribution[key],
            "percentage": _ratio(meal_distribution[key], total_meal_distribution),
            "color": meal_colors[key],
        }
        for key in ["breakfast", "lunch", "dinner", "snack"]
    ]

    weekday_pattern = [
        {
            "key": label,
            "label": label,
            "energy": _to_number(data["energy"], 0),
            "protein": _to_number(data["protein"]),
            "meals": data["meals"],
            "active_days": data["active_days"],
        }
        for label, data in weekday_map.items()
    ]

    heatmap_max_energy = max((_to_number(row["energy"], 0) for row in day_rows.values()), default=0)
    activity_heatmap = [
        {
            "date": str(row["date"]),
            "label": row["label"],
            "weekday": row["weekday"],
            "energy": _to_number(row["energy"], 0),
            "protein": _to_number(row["protein"]),
            "meals": row["meals"],
            "has_record": row["meals"] > 0,
            "intensity": _ratio(_to_number(row["energy"], 0), heatmap_max_energy),
        }
        for row in day_rows.values()
    ]

    meal_completion_items = [
        {
            "key": key,
            "label": meal_labels[key],
            "value": len(meal_completion[key]),
            "expected": 7 if key != "snack" else 4,
            "percentage": _safe_progress(len(meal_completion[key]), 7 if key != "snack" else 4),
            "color": meal_colors[key],
        }
        for key in ["breakfast", "lunch", "dinner", "snack"]
    ]

    goal_labels = {
        "weight_loss": "减重",
        "muscle_gain": "增肌",
        "blood_sugar_control": "控糖",
        "fat_control": "控脂",
        "protein_up": "补蛋白",
        "diet_balance": "饮食均衡",
    }
    goal_progress_items = []
    for goal in goals[:4]:
        records = list(goal.progress_records.all()[:6])
        progress_value = goal.current_value or Decimal("0")
        target_value = goal.target_value or Decimal("0")
        goal_progress_items.append(
            {
                "id": goal.id,
                "label": goal_labels.get(goal.goal_type, goal.goal_type),
                "description": goal.description,
                "progress_percentage": _safe_progress(progress_value, target_value),
                "current_value": _to_number(progress_value),
                "target_value": _to_number(target_value),
                "status": goal.status,
                "target_date": str(goal.target_date) if goal.target_date else "",
                "progress_points": [
                    {
                        "date": str(item.progress_date),
                        "label": str(item.progress_date)[5:],
                        "value": _to_number(item.progress_value),
                        "note": item.note,
                    }
                    for item in records
                ],
            }
        )

    insights = [
        {
            "title": "这周最该关注的不是图表数量，而是记录连续性",
            "description": f"最近 7 天活跃 {week['active_days']} 天、完成 {week['meals']} 餐，连续性越稳，所有趋势图越可信。",
            "tone": "primary",
        },
        {
            "title": "营养结构决定了复盘质量",
            "description": f"近 14 天三大营养素中，蛋白占比 {next((item['percentage'] for item in macro_distribution if item['key'] == 'protein'), 0)}%，可结合目标继续调整。",
            "tone": "accent",
        },
        {
            "title": "把记录沉淀成菜谱和报表，系统才会越用越快",
            "description": f"近 7 天菜谱带入率约 {week['recipe_link_rate']}%，已完成报表 {report_assets['completed']} 份，说明资产化空间还存在。",
            "tone": "success",
        },
    ]

    return {
        "generated_at": timezone.now().isoformat(),
        "targets": {
            "calorie_target": _to_number(calorie_target, 0),
            "protein_target": _to_number(protein_target),
            "fat_target": _to_number(nutrition_targets.get("fat_target")),
            "carb_target": _to_number(nutrition_targets.get("carb_target")),
            "fiber_target": _to_number(nutrition_targets.get("fiber_target")),
            "sodium_limit": _to_number(nutrition_targets.get("sodium_limit"), 0),
            "calcium_target": _to_number(nutrition_targets.get("calcium_target"), 0),
            "iron_target": _to_number(nutrition_targets.get("iron_target")),
            "vitamin_c_target": _to_number(nutrition_targets.get("vitamin_c_target"), 0),
            "goal_hint": nutrition_targets.get("goal_hint") or "",
            "bmi": _to_number(nutrition_targets.get("bmi")) if nutrition_targets.get("bmi") is not None else 0,
            "balance_score": nutrition_targets.get("balance_score"),
            "adequacy": nutrition_targets.get("adequacy") or {},
        },
        "period_overview": {
            "week": week,
            "fortnight": fortnight,
            "month": month,
        },
        "headline_cards": headline_cards,
        "charts": {
            "daily_nutrition_trend": trend_rows,
            "meal_distribution": meal_distribution_items,
            "macro_distribution": macro_distribution,
            "weekday_pattern": weekday_pattern,
            "activity_heatmap": activity_heatmap,
            "meal_completion": meal_completion_items,
        },
        "goals": goal_progress_items,
        "report_assets": report_assets,
        "insights": insights,
    }
