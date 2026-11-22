from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('escape_arenas', '0005_escape_world')]
    operations = [
        migrations.AddField(model_name='userescapesession', name='active_elapsed_seconds', field=models.FloatField(default=0)),
        migrations.AddField(model_name='userescapesession', name='active_since', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='userescapesession', name='pause_count', field=models.PositiveIntegerField(default=0)),
    ]
