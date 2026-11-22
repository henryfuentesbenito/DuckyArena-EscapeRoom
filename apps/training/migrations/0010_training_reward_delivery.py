from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('training', '0009_define_exercise_ten')]
    operations = [migrations.CreateModel(name='TrainingRewardDelivery', fields=[
        ('id', models.BigAutoField(primary_key=True, serialize=False)),
        ('status', models.CharField(max_length=16, default='PENDING', choices=[(x,x) for x in ('PENDING','APPLIED','NO_REWARD','FAILED')])),
        ('xp_amount', models.PositiveIntegerField(default=0)),
        ('coin_amount', models.PositiveIntegerField(default=0)),
        ('last_error', models.TextField(blank=True)),
        ('updated_at', models.DateTimeField(auto_now=True)),
        ('attempt', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='reward_delivery', to='training.trainingattempt')),
    ])]
