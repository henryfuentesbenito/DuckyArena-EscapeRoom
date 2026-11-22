from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("ecomotor", "0008_training_specialization_xp")]
    operations = [migrations.CreateModel(name="PlayerStatPlan", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("stage_code", models.CharField(max_length=32)),
        ("active_branch", models.CharField(blank=True, max_length=32)),
        ("allocations", models.JSONField(default=dict)),
        ("branch_allocations", models.JSONField(default=dict)),
        ("specialization_notice_pending", models.BooleanField(default=False)),
        ("profile", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="stat_plan", to="users.userprofileecomotor")),
    ])]
