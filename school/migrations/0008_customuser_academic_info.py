from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("school", "0007_sitestat"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="academic_info",
            field=models.CharField(blank=True, max_length=100, verbose_name="Sinf yoki fan"),
        ),
    ]
