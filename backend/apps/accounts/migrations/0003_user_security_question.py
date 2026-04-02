from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_email_alter_user_username"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="security_question",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="user",
            name="security_answer_hash",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
