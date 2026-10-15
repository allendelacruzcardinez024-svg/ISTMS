from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0005_assign_departments_to_named_users"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="issue_type",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
