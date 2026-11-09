from django.db import migrations, models


def migrate_approved_statuses(apps, schema_editor):
    Application = apps.get_model("school", "Application")
    Application.objects.filter(status="approved").update(status="accepted")


class Migration(migrations.Migration):

    dependencies = [
        ("school", "0008_customuser_academic_info"),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Kutilmoqda"),
                    ("interview", "Suhbatga chaqirildi"),
                    ("accepted", "Qabul qilindi"),
                    ("rejected", "Rad etildi"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_approved_statuses, migrations.RunPython.noop),
    ]
