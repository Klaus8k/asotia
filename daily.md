### VS Code — оставить
Добавь только расширения:

Python (Microsoft) — обязательно
Pylance — автодополнение, типизация
Django (Baptiste Darthenay) — подсветка шаблонов
DotENV — подсветка .env файлов
GitLens — удобная работа с git

### Чего не хватает — Docker Desktop
Для локальной разработки очень рекомендую. Вместо того чтобы устанавливать PostgreSQL и Redis на Windows — запускаешь их в контейнерах одной командой:

'''
yaml# docker-compose.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: foodshop
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
bashdocker-compose up -d
'''

И всё — PostgreSQL и Redis работают локально, DBeaver к ним подключается как обычно. На Windows без Docker установка этих сервисов — лишняя головная боль.