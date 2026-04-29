from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("models", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="channel_chat_id",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="task",
            name="channel_message_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
