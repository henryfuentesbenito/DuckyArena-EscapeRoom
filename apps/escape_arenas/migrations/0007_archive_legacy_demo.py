from django.db import migrations


def archive_legacy(apps, schema_editor):
    EscapeRoom = apps.get_model("escape_arenas", "EscapeRoom")
    EscapeRoom.objects.filter(slug="escape-demo-seis-fases").update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [("escape_arenas", "0006_session_clock")]
    operations = [migrations.RunPython(archive_legacy, migrations.RunPython.noop)]
