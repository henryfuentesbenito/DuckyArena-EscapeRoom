from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("escape_arenas", "0004_escaperoom_era")]
    operations = [
        migrations.CreateModel(name="EscapeItemDefinition", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("key", models.SlugField(max_length=100)), ("name", models.CharField(max_length=120)),
            ("description", models.TextField(blank=True)), ("asset_key", models.CharField(blank=True, max_length=160)),
            ("escape_room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="item_definitions", to="escape_arenas.escaperoom"))]),
        migrations.CreateModel(name="EscapeInteractable", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("key", models.SlugField(max_length=100)), ("label", models.CharField(max_length=120)),
            ("asset_key", models.CharField(blank=True, max_length=160)), ("x", models.FloatField(default=0.5)),
            ("y", models.FloatField(default=0.5)), ("actions", models.JSONField(blank=True, default=dict)),
            ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interactables", to="escape_arenas.room"))]),
        migrations.CreateModel(name="EscapeSessionItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("quantity", models.PositiveIntegerField(default=1)),
            ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="escape_arenas.escapeitemdefinition")),
            ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="world_items", to="escape_arenas.userescapesession"))]),
        migrations.CreateModel(name="EscapeWorldState", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("state", models.CharField(default="idle", max_length=40)),
            ("interactable", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="escape_arenas.escapeinteractable")),
            ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="world_states", to="escape_arenas.userescapesession"))]),
        migrations.AddConstraint(model_name="escapeitemdefinition", constraint=models.UniqueConstraint(fields=("escape_room", "key"), name="escape_item_unique_key")),
        migrations.AddConstraint(model_name="escapeinteractable", constraint=models.UniqueConstraint(fields=("room", "key"), name="escape_interactable_unique_key")),
        migrations.AddConstraint(model_name="escapesessionitem", constraint=models.UniqueConstraint(fields=("session", "item"), name="escape_session_item_unique")),
        migrations.AddConstraint(model_name="escapeworldstate", constraint=models.UniqueConstraint(fields=("session", "interactable"), name="escape_world_state_unique")),
    ]
