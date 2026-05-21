## 17. Безопасность production

Обязательно:

1. `DEBUG=False`.
2. Сильный `SECRET_KEY`.
3. `ALLOWED_HOSTS=asotia.ru,www.asotia.ru`.
4. `CSRF_TRUSTED_ORIGINS=https://asotia.ru,https://www.asotia.ru`.
5. Секреты только в `.env`.
6. `.env` не хранить в git.
7. PostgreSQL не открывать наружу.
8. Доступ к VPS только по SSH.
9. SSL-сертификат через Certbot.
10. Регулярные backup PostgreSQL.
11. Регулярные backup директории `media/`.

Желательно:

1. Отдельный Linux-пользователь под проект.
2. Ограниченные права на директории.
3. Логи приложения отдельно от nginx-логов.
4. Мониторинг свободного места на диске.
5. Проверка срока действия SSL.

---

---

## 18. Backup

Минимальная схема backup:

```bash
pg_dump asoti_foodshop > /backup/asoti_foodshop_$(date +%F).sql
tar -czf /backup/asoti_media_$(date +%F).tar.gz /var/www/asoti-foodshop/media/
```

Что бэкапить:
- базу PostgreSQL;
- папку `media/`;
- production `.env`;
- nginx config;
- systemd service.

Что не обязательно бэкапить:
- `.venv`;
- `staticfiles`;
- кэш;
- временные файлы.

---
