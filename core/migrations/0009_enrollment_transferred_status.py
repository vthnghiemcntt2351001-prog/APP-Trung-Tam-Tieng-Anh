from django.db import migrations, models


def replace_paused_with_stopped(apps, schema_editor):
    Enrollment = apps.get_model("core", "Enrollment")
    Enrollment.objects.using(schema_editor.connection.alias).filter(
        status="paused"
    ).update(status="stopped")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_enrollment"),
    ]

    operations = [
        migrations.RunPython(
            replace_paused_with_stopped,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="status",
            field=models.CharField(
                choices=[
                    ("studying", "Đang học"),
                    ("transferred", "Đã chuyển lớp"),
                    ("stopped", "Đã dừng"),
                    ("completed", "Hoàn thành"),
                ],
                default="studying",
                max_length=20,
                verbose_name="Trạng thái ghi danh",
            ),
        ),
    ]
