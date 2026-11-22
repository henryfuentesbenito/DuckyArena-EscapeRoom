from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator

class Migration(migrations.Migration):
    dependencies = [('ecomotor', '0007_target_catalog_freeze'), ('users', '0002_ecomotor_progress')]
    operations = [migrations.CreateModel(name='SpecializationXPEvent', fields=[
        ('id', models.BigAutoField(primary_key=True, serialize=False)),
        ('operation_key', models.CharField(max_length=255)),
        ('amount', models.PositiveBigIntegerField(validators=[MinValueValidator(1)])),
        ('xp_before', models.PositiveBigIntegerField()),
        ('xp_after', models.PositiveBigIntegerField()),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('profile', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='specialization_xp_events', to='users.userprofileecomotor')),
        ('progress', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='xp_events', to='ecomotor.userspecializationprogress')),
    ], options={'constraints': [
        models.UniqueConstraint(fields=['profile','operation_key'], name='ecomotor_spec_xp_profile_key'),
        models.CheckConstraint(condition=models.Q(amount__gt=0), name='ecomotor_spec_xp_positive'),
        models.CheckConstraint(condition=models.Q(xp_after=models.F('xp_before')+models.F('amount')), name='ecomotor_spec_xp_snapshot'),
    ]})]
