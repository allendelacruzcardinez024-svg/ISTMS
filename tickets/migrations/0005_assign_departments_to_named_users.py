from django.db import migrations


def assign_named_user_departments(apps, schema_editor):
    Profile = apps.get_model("tickets", "Profile")
    assignments = {
        "ALLEN JOHN DELA CRUZ CARDINEZ": "Information Technology",
        "manager": "IT Support Services",
        "juan": "Network and Infrastructure",
        "employee": "Human Resources",
        "admin": "Operations",
    }
    for username, department in assignments.items():
        Profile.objects.filter(user__username__iexact=username).update(department=department)


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0004_profile_department_choices"),
    ]

    operations = [
        migrations.RunPython(assign_named_user_departments, migrations.RunPython.noop),
    ]