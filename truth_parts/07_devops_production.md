## 1. Домены и окружения

### Production-домен

- Основной домен: `asotia.ru`
- Дополнительный домен: `www.asotia.ru`
- Основной вариант для сайта: `asotia.ru`
- Редирект: `www.asotia.ru` → `asotia.ru`

### Окружения

| Окружение | Назначение | Где находится |
|----------|------------|---------------|
| local/dev | локальная разработка | Windows 10 + VS Code + Docker |
| production | рабочий сайт | VPS + Nginx + Gunicorn |

---

---

## 14. Production-инфраструктура

### VPS

- OS: Ubuntu 22.04 LTS
- Домен: `asotia.ru`
- Путь к проекту: `/var/www/asoti-foodshop`

### Nginx

- Config: `/etc/nginx/sites-available/asoti-foodshop`
- Symlink: `/etc/nginx/sites-enabled/asoti-foodshop`
- Logs:
  - `/var/log/nginx/asoti_access.log`
  - `/var/log/nginx/asoti_error.log`

### Gunicorn

- Socket: `/run/asoti-foodshop.sock`
- Service: `/etc/systemd/system/asoti-foodshop.service`
- Workers: 2–3 для текущей нагрузки достаточно

### Пути на сервере

- Проект: `/var/www/asoti-foodshop`
- Виртуальное окружение: `/var/www/asoti-foodshop/.venv`
- Статика: `/var/www/asoti-foodshop/staticfiles/`
- Медиа: `/var/www/asoti-foodshop/media/`
- Логи приложения: `/var/www/asoti-foodshop/logs/`

---

---

## 15. Nginx — базовая схема

```nginx
server {
    listen 80;
    server_name asotia.ru www.asotia.ru;

    location /static/ {
        alias /var/www/asoti-foodshop/staticfiles/;
    }

    location /media/ {
        alias /var/www/asoti-foodshop/media/;
    }

    location / {
        proxy_pass http://unix:/run/asoti-foodshop.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

После подключения SSL через Certbot основной конфиг должен работать по HTTPS.

---

---

## 16. systemd service

```ini
[Unit]
Description=Asoti Food Shop Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/asoti-foodshop
Environment="DJANGO_SETTINGS_MODULE=config.settings.prod"
ExecStart=/var/www/asoti-foodshop/.venv/bin/gunicorn config.wsgi:application \
    --workers 3 \
    --bind unix:/run/asoti-foodshop.sock

Restart=always

[Install]
WantedBy=multi-user.target
```

Команды:

```bash
sudo systemctl daemon-reload
sudo systemctl enable asoti-foodshop
sudo systemctl start asoti-foodshop
sudo systemctl restart asoti-foodshop
sudo systemctl status asoti-foodshop
```

---
