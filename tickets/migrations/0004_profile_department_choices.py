from django.db import migrations, models


def normalize_departments(apps, schema_editor):
    Profile = apps.get_model("tickets", "Profile")
    department_mapping = {
        "Information and Communication Technology": "Information Technology",
        "IT": "Information Technology",
        "IT Support": "IT Support Services",
        "Hardware Support": "IT Support Services",
        "IT Access Support": "IT Support Services",
        "Software Support": "IT Support Services",
        "Printer Support": "IT Support Services",
        "Network Support": "Network and Infrastructure",
    }
    for old_department, new_department in department_mapping.items():
        Profile.objects.filter(department=old_department).update(department=new_department)


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0003_notification"),
    ]

    operations = [
        migrations.RunPython(normalize_departments, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="profile",
            name="department",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Information Technology", "Information Technology"),
                    ("IT Support Services", "IT Support Services"),
                    ("Network and Infrastructure", "Network and Infrastructure"),
                    ("Human Resources", "Human Resources"),
                    ("Operations", "Operations"),
                ],
                max_length=100,
            ),
        ),
    ]