import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def migrate_existing_class_memberships(apps, schema_editor):
    Enrollment = apps.get_model("core", "Enrollment")
    EnglishClass = apps.get_model("core", "EnglishClass")
    db_alias = schema_editor.connection.alias

    students_field = EnglishClass._meta.get_field("students")
    old_membership = students_field.remote_field.through
    class_field_name = students_field.m2m_field_name()
    student_field_name = students_field.m2m_reverse_field_name()
    class_start_dates = dict(
        EnglishClass.objects.using(db_alias).values_list("pk", "start_date")
    )

    rows = []
    for membership in old_membership.objects.using(db_alias).iterator():
        class_id = getattr(membership, f"{class_field_name}_id")
        student_id = getattr(membership, f"{student_field_name}_id")
        rows.append(
            Enrollment(
                student_id=student_id,
                english_class_id=class_id,
                status="studying",
                # Existing M2M rows have no enrollment date; class start is
                # the least surprising migration fallback.
                enrolled_at=class_start_dates[class_id],
            )
        )

    Enrollment.objects.using(db_alias).bulk_create(rows, batch_size=500)


def restore_existing_class_memberships(apps, schema_editor):
    Enrollment = apps.get_model("core", "Enrollment")
    EnglishClass = apps.get_model("core", "EnglishClass")
    db_alias = schema_editor.connection.alias

    students_field = EnglishClass._meta.get_field("students")
    old_membership = students_field.remote_field.through
    class_field_name = students_field.m2m_field_name()
    student_field_name = students_field.m2m_reverse_field_name()

    rows = (
        old_membership(
            **{
                f"{class_field_name}_id": class_id,
                f"{student_field_name}_id": student_id,
            }
        )
        for student_id, class_id in Enrollment.objects.using(db_alias).values_list(
            "student_id", "english_class_id"
        )
    )
    old_membership.objects.using(db_alias).bulk_create(rows, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_certificate"),
    ]

    operations = [
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("studying", "Đang học"),
                            ("paused", "Tạm dừng"),
                            ("stopped", "Đã dừng"),
                            ("completed", "Hoàn thành"),
                        ],
                        default="studying",
                        max_length=20,
                        verbose_name="Trạng thái ghi danh",
                    ),
                ),
                (
                    "enrolled_at",
                    models.DateField(
                        default=django.utils.timezone.localdate,
                        verbose_name="Ngày ghi danh",
                    ),
                ),
                (
                    "ended_at",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Ngày kết thúc",
                    ),
                ),
                ("note", models.TextField(blank=True, verbose_name="Ghi chú")),
                (
                    "english_class",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="core.englishclass",
                        verbose_name="Lớp học",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="core.student",
                        verbose_name="Học viên",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ghi danh",
                "verbose_name_plural": "Danh sách ghi danh",
                "ordering": ["-enrolled_at", "student__full_name"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("student", "english_class"),
                        name="unique_student_class_enrollment",
                    )
                ],
            },
        ),
        migrations.RunPython(
            migrate_existing_class_memberships,
            restore_existing_class_memberships,
        ),
        migrations.RemoveField(
            model_name="englishclass",
            name="students",
        ),
        migrations.AddField(
            model_name="englishclass",
            name="students",
            field=models.ManyToManyField(
                blank=True,
                related_name="english_classes",
                through="core.Enrollment",
                to="core.student",
                verbose_name="Học viên",
            ),
        ),
    ]
