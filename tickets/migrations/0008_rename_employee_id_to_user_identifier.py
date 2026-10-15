from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0007_profile_profile_picture_alter_profile_role"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="employee_id",
            new_name="user_identifier",
        ),
        migrations.AlterField(
            model_name="profile",
            name="user_identifier",
            field=models.CharField(blank=True, max_length=50, verbose_name="User ID"),
        ),
    ]
