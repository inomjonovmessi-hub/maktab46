from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("school", "0003_alter_application_desired_grade"),
    ]

    operations = [
        migrations.RenameField(
            model_name="application",
            old_name="child_name",
            new_name="student_name",
        ),
        migrations.RenameField(
            model_name="application",
            old_name="desired_grade",
            new_name="grade_level",
        ),
        migrations.RenameField(
            model_name="application",
            old_name="parent_phone",
            new_name="phone",
        ),
        migrations.RemoveField(
            model_name="application",
            name="parent_name",
        ),
        migrations.RemoveField(
            model_name="application",
            name="address",
        ),
    ]
