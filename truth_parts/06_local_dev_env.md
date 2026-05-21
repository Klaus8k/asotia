## 11. Локальное окружение Windows 10

### Инструменты

- VS Code
- Расширения VS Code:
  - Python
  - Pylance
  - Django
  - DotENV
  - GitLens
- Windows Terminal
- Docker Desktop
- DBeaver
- Git
- WinSCP только для аварийных случаев

### Локальные сервисы

Локально через Docker запускаются:

- PostgreSQL
- Redis, если понадобится

Django запускается локально через Poetry.

---

---

## 12. docker-compose.yml для dev

```yaml
services:
  db:
    image: postgres:15
    container_name: asoti_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-foodshop}
      POSTGRES_USER: ${POSTGRES_USER:-foodshop}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-foodshop}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    container_name: asoti_redis
    restart: unless-stopped
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

Запуск:

```bash
docker compose up -d
```

Остановка:

```bash
docker compose down
```

---

---

## 13. .env

### .env.example

```env
DEBUG=True
SECRET_KEY=change-me

ALLOWED_HOSTS=127.0.0.1,localhost

DATABASE_URL=postgres://foodshop:foodshop@127.0.0.1:5432/foodshop

POSTGRES_DB=foodshop
POSTGRES_USER=foodshop
POSTGRES_PASSWORD=foodshop

REDIS_URL=redis://127.0.0.1:6379/0
```

### Production .env

```env
DEBUG=False
SECRET_KEY=strong-production-secret-key

ALLOWED_HOSTS=asotia.ru,www.asotia.ru

DATABASE_URL=postgres://db_user:db_password@127.0.0.1:5432/asoti_foodshop

REDIS_URL=redis://127.0.0.1:6379/0
```

Правила:
- `.env` никогда не пушить в git;
- `.env.example` можно и нужно хранить в git;
- реальные пароли хранить в Bitwarden / другом менеджере паролей;
- не хранить production `.env` в открытом облаке.

---
