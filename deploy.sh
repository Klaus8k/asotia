#!/usr/bin/env bash

set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-asotia}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-}"
EXPECTED_DATABASE_HOST="${EXPECTED_DATABASE_HOST:-127.0.0.1}"
EXPECTED_DATABASE_PORT="${EXPECTED_DATABASE_PORT:-15432}"

log() {
    printf '[deploy] %s\n' "$1"
}

fail() {
    printf '[deploy] ERROR: %s\n' "$1" >&2
    exit 1
}

run_systemctl() {
    if [[ "${EUID}" -eq 0 ]]; then
        systemctl "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo systemctl "$@"
    else
        fail "Для управления systemd нужен root или команда sudo."
    fi
}

trap 'fail "Сбой на строке ${LINENO}. Деплой остановлен."' ERR

command -v git >/dev/null 2>&1 || fail "Не найден git."
command -v poetry >/dev/null 2>&1 || fail "Не найден Poetry."
command -v systemctl >/dev/null 2>&1 || fail "Не найден systemctl."

[[ -d "${APP_DIR}/.git" ]] || fail "${APP_DIR} не является Git-репозиторием."
[[ -f "${APP_DIR}/.env" ]] || fail "Не найден production-файл ${APP_DIR}/.env."

cd "${APP_DIR}"

CURRENT_BRANCH="$(git branch --show-current)"
[[ "${CURRENT_BRANCH}" == "${BRANCH}" ]] || fail \
    "Текущая ветка ${CURRENT_BRANCH:-detached HEAD}, ожидалась ${BRANCH}."

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    fail "Есть локальные изменения отслеживаемых файлов. Деплой отменён."
fi

log "Получаю origin/${BRANCH}."
git fetch --prune origin "${BRANCH}"

log "Обновляю код только через fast-forward."
git merge --ff-only "origin/${BRANCH}"

log "Устанавливаю production-зависимости."
poetry install --only main --no-root --no-interaction --no-ansi

export DJANGO_SETTINGS_MODULE="config.settings.prod"

DATABASE_ENDPOINT="$(
    poetry run python -c '
import django

django.setup()

from django.conf import settings

database = settings.DATABASES["default"]
print(
    "{}:{}".format(
        database.get("HOST") or "localhost",
        database.get("PORT") or 5432,
    )
)
'
)"
EXPECTED_DATABASE_ENDPOINT="${EXPECTED_DATABASE_HOST}:${EXPECTED_DATABASE_PORT}"
[[ "${DATABASE_ENDPOINT}" == "${EXPECTED_DATABASE_ENDPOINT}" ]] || fail \
    "DATABASE_URL указывает ${DATABASE_ENDPOINT}, ожидался ${EXPECTED_DATABASE_ENDPOINT}."

log "Проверяю production-конфигурацию Django."
poetry run python manage.py check --deploy

log "Применяю миграции."
poetry run python manage.py migrate --noinput

log "Собираю статические файлы."
poetry run python manage.py collectstatic --noinput

log "Перезапускаю systemd-сервис ${SERVICE_NAME}."
run_systemctl restart "${SERVICE_NAME}"
run_systemctl is-active --quiet "${SERVICE_NAME}"

if [[ -n "${HEALTHCHECK_URL}" ]]; then
    command -v curl >/dev/null 2>&1 || fail \
        "Для HEALTHCHECK_URL нужна команда curl."

    log "Проверяю ${HEALTHCHECK_URL}."
    curl \
        --fail \
        --silent \
        --show-error \
        --retry 5 \
        --retry-delay 2 \
        "${HEALTHCHECK_URL}" >/dev/null
fi

log "Деплой завершён успешно."
