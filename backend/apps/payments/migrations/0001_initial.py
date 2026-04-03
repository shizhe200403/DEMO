from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0004_user_plan_quota"),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_no",   models.CharField(db_index=True, max_length=64, unique=True)),
                ("plan_type",  models.CharField(
                    choices=[("monthly", "月度套餐 ¥25"), ("annual", "年度套餐 ¥199")],
                    default="monthly", max_length=16)),
                ("amount",     models.DecimalField(decimal_places=2, max_digits=8)),
                ("status",     models.CharField(
                    choices=[("pending", "待支付"), ("paid", "已支付"),
                              ("cancelled", "已取消"), ("refunded", "已退款")],
                    default="pending", max_length=16)),
                ("trade_no",   models.CharField(blank=True, default="", max_length=128)),
                ("plan_start", models.DateTimeField(blank=True, null=True)),
                ("plan_end",   models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="orders", to="accounts.user")),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "订单", "verbose_name_plural": "订单"},
        ),
    ]
