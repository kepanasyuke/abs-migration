# АБС-Миграция — бэкенд и приложение

Платформа миграции банковских данных из legacy-АБС в ЦФТ-Банк (IBSO):
FastAPI поверх SQLite `api/mig.db`, логика взята из протестированных модулей `cases/`.

## Запуск

```cmd
run-api.cmd
```

или вручную из этой папки:

```cmd
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

- Интерфейс (оконное приложение, тот же origin): <http://127.0.0.1:8000/app>
- OpenAPI: <http://127.0.0.1:8000/docs>
- Проверка живости: <http://127.0.0.1:8000/api/v1/health>

Если API не запущен, `../abs-migration-desktop.html` открывается в демо-режиме
на встроенных данных — интерфейс остаётся работоспособным.

## Проверки

```cmd
python -m pytest -q            :: 2 102 теста по 8 кейсам
python -m ruff check api cases tests conftest.py
```

## Маршруты

| Метод | Путь | Сервис |
| --- | --- | --- |
| GET | `/api/v1/health` | gateway |
| GET | `/api/v1/s2t/fields?wave=5` | s2t-svc |
| POST | `/api/v1/s2t/confirm` | s2t-svc |
| GET | `/api/v1/dq/scan/{table}` | dq-svc |
| GET | `/api/v1/recon/{wave}` | recon-svc |
| GET | `/api/v1/rules`, POST `/api/v1/rules/compile` | rule-svc |
| GET | `/api/v1/postings/balance` | posting-svc |
| GET | `/api/v1/cutover/{run}`, POST `/api/v1/cutover/controls`, POST `/api/v1/cutover/schedule` | cutover-svc |
| POST | `/api/v1/assist/ask` | assist-svc |
| GET | `/api/v1/tower/readiness` | tower-svc |
| GET | `/api/v1/services`, `/api/v1/waves`, `/api/v1/docs` | gateway |
| POST | `/api/v1/waves/{n}/start`, `/api/v1/admin/reset` | gateway |

## Данные

`api/store.py` — схема и детерминированные сиды: 12 legacy-полей, 12 целевых полей ЦФТ,
6 клиентов, 8 остатков по волнам 4–5, 5 проводок, 5 правил, 5 документов регламентов,
9 сервисов, 6 волн, контроли и шаги cut-over. Пересоздать базу: `POST /api/v1/admin/reset`.
