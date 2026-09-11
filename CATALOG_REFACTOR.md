# Переработка каталога: перенос и восстановление

## Резервные данные

Перед изменением локальной базы созданы:

- `backups/catalog-refactor-2026-09-11/foodshop-before.dump` — полный дамп
  PostgreSQL в custom format;
- `backups/catalog-refactor-2026-09-11/catalog-before-utf8.json` — UTF-8-снимок
  11 актуальных категорий и 64 актуальных товаров.

Дамп проверен командой `pg_restore -l` и тестовым восстановлением в отдельную
локальную БД `foodshop_restore_check`. После восстановления подтверждены 64
товара, 11 категорий, 2 пользователя, 8 заказов и 12 позиций заказов. Каталог
`backups/` исключён из Git и должен храниться локально с подходящими правами.

SHA-256:

- `foodshop-before.dump`:
  `139DE65F38FDC84377F169E95D1F8F4092A2E893AA8C30BB6E74DD67ADF70E67`;
- `catalog-before-utf8.json`:
  `AC98536F7416C50286AFA5AEDC2C5B925225FDE8BCFDA4D858A1C12454F3C21B`.

Для полного отката старую базу следует восстанавливать только после отдельной
проверки имени и окружения. Локальный сценарий для контейнера проекта:

```powershell
docker cp backups/catalog-refactor-2026-09-11/foodshop-before.dump `
  asoti_postgres:/tmp/foodshop-before.dump
docker exec asoti_postgres pg_restore --exit-on-error --clean --if-exists `
  -U foodshop -d foodshop /tmp/foodshop-before.dump
```

Команда с `--clean` удаляет объекты целевой базы, поэтому её нельзя запускать,
пока не подтверждено, что целью является локальная `foodshop` проекта.

## Импорт в новую схему

После применения чистых миграций актуальный каталог импортируется так:

```powershell
poetry run python -X utf8 manage.py import_catalog_snapshot `
  backups/catalog-refactor-2026-09-11/catalog-before-utf8.json `
  --report catalog_manual_review.md
```

Правила преобразования:

- `storage_type=canned/frozen/other` превращается в категорию
  «Консервы»/«Заморозка»/«Другое»;
- известный `product_type` превращается в значение «Вид продукции»;
- известный `meat_type`, кроме `none`, превращается в «Основной ингредиент»;
- очевидные конина, утка, тунец, минтай, треска и кальмар распознаются по
  названию; спорные значения не угадываются;
- «Без мяса» автоматически не назначается;
- имена, описания, цены, остатки, активность, даты и пути к изображениям
  сохраняются из актуальной `catalog_product`.

Результат и список неоднозначных товаров находятся в
`catalog_manual_review.md`.
