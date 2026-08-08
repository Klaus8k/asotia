from django.db import migrations


EMAIL_INDEX_NAME = "asotia_auth_user_email_ci_uniq"


def normalize_user_emails(apps, schema_editor):
    User = apps.get_model("auth", "User")
    normalized_by_id = {}
    owners = {}

    for user_id, email in User.objects.order_by("pk").values_list("pk", "email"):
        normalized = email.strip().lower()
        if normalized and normalized in owners:
            raise RuntimeError(
                "Найдены пользователи с одинаковым email без учета регистра. "
                "Устраните дубликаты перед применением миграции."
            )
        if normalized:
            owners[normalized] = user_id
        normalized_by_id[user_id] = normalized

    for user_id, normalized in normalized_by_id.items():
        User.objects.filter(pk=user_id).update(email=normalized)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(normalize_user_emails, migrations.RunPython.noop),
        migrations.RunSQL(
            sql=(
                f'CREATE UNIQUE INDEX "{EMAIL_INDEX_NAME}" '
                'ON "auth_user" (LOWER("email")) WHERE "email" <> \'\''
            ),
            reverse_sql=f'DROP INDEX IF EXISTS "{EMAIL_INDEX_NAME}"',
        ),
    ]
