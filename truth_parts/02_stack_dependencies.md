## 2. Стек и версии

| Компонент       | Версия / решение | Примечание |
|-----------------|------------------|-----------|
| Python          | 3.12.x | стабильная версия для нового проекта |
| Django          | 5.2.x LTS | LTS-ветка |
| PostgreSQL      | 15.x | стабильная версия, достаточно для проекта |
| Redis           | 7.x | позже: кэш, сессии, Celery; на MVP можно без него |
| Celery          | 5.x | не в первом MVP, добавить позже |
| Gunicorn        | актуальная стабильная | production WSGI-сервер |
| Nginx           | из репозитория Ubuntu | reverse proxy + static/media |
| Ubuntu Server   | 22.04 LTS | текущая целевая ОС VPS |
| Docker Desktop  | latest | локальная разработка PostgreSQL + Redis |
| Poetry          | 1.8.x | управление зависимостями |

---

---

## 9. Зависимости

Управление зависимостями — через Poetry.

Файл `requirements.txt` вручную не редактировать.
Если он понадобится для деплоя, генерировать из Poetry.

### Основные команды

```bash
poetry install
poetry add <package>
poetry add --group dev <package>
poetry remove <package>
poetry update
poetry shell
```

На VPS:

```bash
poetry install --only main
```

---

---

## 10. pyproject.toml

```toml
[tool.poetry]
name = "asoti-foodshop"
version = "0.1.0"
description = "Asoti food shop"
authors = ["Asoti"]
package-mode = false

[tool.poetry.dependencies]
python = "^3.12"
django = "^5.2"
psycopg2-binary = "^2.9"
pillow = "^10.0"
django-environ = "^0.11"
gunicorn = "^21.0"

# Stage 2
# redis = "^5.0"
# celery = "^5.3"
# django-filter = "^24.0"

[tool.poetry.group.dev.dependencies]
django-debug-toolbar = "*"
pytest = "*"
pytest-django = "*"
ruff = "*"
```

---
