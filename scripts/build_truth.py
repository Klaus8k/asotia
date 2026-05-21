# scripts/build_truth.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PARTS_DIR = BASE_DIR / "truth_parts"
OUTPUT_FILE = BASE_DIR / "CLAUDE.md"

FILES = [
    "00_index.md",
    "01_project_mvp.md",
    "02_stack_dependencies.md",
    "03_architecture_apps_urls.md",
    "04_database_models.md",
    "05_django_settings.md",
    "06_local_dev_env.md",
    "07_devops_production.md",
    "08_security_backup.md",
    "09_admin_orders_notifications.md",
    "10_code_git_limits.md",
]

content = []

for filename in FILES:
    path = PARTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Нет файла: {path}")

    content.append(path.read_text(encoding="utf-8").strip())

OUTPUT_FILE.write_text("\n\n---\n\n".join(content) + "\n", encoding="utf-8")

print(f"Готово: {OUTPUT_FILE}")