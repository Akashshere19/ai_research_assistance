
from django.conf import settings
from django.db import migrations, models


def populate_normalized_content(apps, schema_editor):
    LongTermMemory = apps.get_model(
        "conversations",
        "LongTermMemory",
    )
    database = schema_editor.connection.alias

    memories = LongTermMemory.objects.using(database).all()

    for memory in memories.iterator():
        memory.normalized_content = memory.content.strip().casefold()
        memory.save(update_fields=["normalized_content"])


class Migration(migrations.Migration):

    dependencies = [
        ("agents_runs", "0006_agentrun_conversation"),
        ("conversations", "0002_longtermmemory"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="longtermmemory",
            name="normalized_content",
            field=models.CharField(
                blank=True,
                default="",
                max_length=2000,
            ),
        ),
        migrations.RunPython(
            populate_normalized_content,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="longtermmemory",
            constraint=models.UniqueConstraint(
                condition=models.Q(memory_type="PREFERENCE"),
                fields=("user", "normalized_content"),
                name="unique_user_preference_normalized",
            ),
        ),
    ]
