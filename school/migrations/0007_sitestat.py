from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("school", "0006_book_directorfeedback_facility_schoolclub_teacher_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteStat",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("total_views", models.PositiveBigIntegerField(default=0, verbose_name="Jami tashriflar")),
                (
                    "unique_visitors",
                    models.PositiveBigIntegerField(default=0, verbose_name="Noyob tashrif buyuruvchilar"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Sayt statistikasi",
                "verbose_name_plural": "Sayt statistikasi",
            },
        ),
    ]
