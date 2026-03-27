from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from apps.tracking.services import build_meal_statistics, build_meal_summary


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

    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    reports_dir = Path(settings.MEDIA_ROOT) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{user.id}_{report_type}_{start_date}_{end_date}.pdf"
    file_path = reports_dir / file_name

    pdf = canvas.Canvas(str(file_path), pagesize=A4)
    _, height = A4

    y = height - 60
    pdf.setFont("STSong-Light", 18)
    pdf.drawString(50, y, "营养健康报告")
    y -= 32
    pdf.setFont("STSong-Light", 11)
    report_type_label = "周报" if report_type == "weekly" else "月报"
    pdf.drawString(50, y, f"报告类型: {report_type_label}")
    y -= 18
    pdf.drawString(50, y, f"统计周期: {start_date} 至 {end_date}")
    y -= 28
    pdf.setFont("STSong-Light", 12)
    pdf.drawString(50, y, "摘要")
    y -= 18
    pdf.setFont("STSong-Light", 11)
    pdf.drawString(50, y, f"总热量: {summary['energy']}")
    y -= 16
    pdf.drawString(50, y, f"蛋白质: {summary['protein']}")
    y -= 16
    pdf.drawString(50, y, f"脂肪: {summary['fat']}")
    y -= 16
    pdf.drawString(50, y, f"碳水: {summary['carbohydrate']}")
    y -= 28
    pdf.setFont("STSong-Light", 12)
    pdf.drawString(50, y, "趋势")
    y -= 18
    pdf.setFont("STSong-Light", 10)
    for row in trend[:20]:
        pdf.drawString(50, y, f"{row['date']}: 热量={row['energy']} 蛋白质={row['protein']}")
        y -= 14
        if y < 60:
            pdf.showPage()
            y = height - 50

    pdf.save()
    return file_path
