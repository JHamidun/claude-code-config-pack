# your-server runbook — backups, rotation, recovery targets, cost

Справочник агента `devops-engineer`. Читать, когда задача касается бэкапов, DR,
ротации секретов или разгрузки сервера. В обычном деплое не нужен.

Сервер: основной хост из `config/server-primary.md` (`ssh your-server`).

## Бэкап баз и томов

Бэкапы разводи по сервисам: каждому свой скрипт и своя строка в root-кроне, окна разнесены
намеренно, чтобы дампы не сходились в один момент — при правке расписания держи этот порядок.
Актуальное расписание смотри в `ssh your-server "crontab -l"`.

Правило 3-2-1: 3 копии, 2 носителя, 1 офсайт.

Каркас ниже — образец для НОВОГО сервиса, а не текст уже работающих скриптов сервера:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/$(date +%Y-%m-%d)"
RETENTION_DAYS=30
mkdir -p "$BACKUP_DIR"

for db in $(docker exec postgres psql -U postgres -t -c "SELECT datname FROM pg_database WHERE datistemplate = false;"); do
  docker exec postgres pg_dump -U postgres "$db" | gzip > "$BACKUP_DIR/${db}.sql.gz"
done

for volume in $(docker volume ls -q); do
  docker run --rm -v "${volume}:/data" -v "$BACKUP_DIR:/backup" \
    alpine tar czf "/backup/vol-${volume}.tar.gz" /data
done

find /opt/backups -type d -mtime +$RETENTION_DAYS -exec rm -rf {} +
# rsync -avz "$BACKUP_DIR" remote:/opt/backups/your-server/   # офсайт-копия
```

Бэкап без проверки восстановления — не бэкап: раз в месяц разворачивать дамп в
тестовый контейнер, раз в квартал — полное восстановление сервиса, раз в год —
пересборка инфраструктуры с нуля.

## Цели восстановления

| Класс сервиса | RTO | RPO |
|---|---|---|
| Критичные (боты, API) | 15 мин | 1 час |
| Важные (админки) | 1 час | 24 часа |
| Обычные (лендинги) | 4 часа | 24 часа |

## Ротация секретов

| Тип | Срок | Как |
|---|---|---|
| API-ключи | 90 дней | перевыпуск в панели провайдера |
| Пароли БД | 180 дней | `ALTER USER` + обновить секреты |
| SSH-ключи | 365 дней | `ssh-keygen`, обновить authorized_keys |
| TLS | авто | certbot renew |
| Ключи подписи JWT | 90 дней | выкатить новый, старый принимать grace-период |

## Разгрузка сервера

Ищи выбросы по памяти, а не среднее:
`docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"`.

- `docker image prune -a --filter "until=168h"` — образы съедают диск быстрее логов;
- `docker volume prune` — только после проверки, что тома ничьи;
- лимиты памяти в compose обязательны: без них один контейнер уносит соседей через OOM;
- критичным сервисам поднять приоритет выживания (`oom_score_adj`);
- alpine-образы там, где нет причин брать полный дистрибутив;
- остановить сервисы, которыми никто не пользуется, — самая дешёвая оптимизация.
