# Handoff — снимок состояния проекта

Файл перезаписывается в конце каждой рабочей сессии. Нужен, чтобы новая сессия
или другой исполнитель быстро понял, где остановились. Долговременные правила —
в `AGENTS.md`, история решений — в `docs/DECISIONS.md`, задачи — в `TODO.md`.

## Состояние на 2026-10-31

- Ветка: `main`, синхронизирована с `origin/main`.
- Последний commit: `97825ab docs: add handoff, decisions, requirements and context links` (влит fast-forward).
- Рабочее дерево: чистое (кроме игнорируемых `.xlsx`/`__pycache__`).
- Python: 3.14.7 (macOS). Зависимости — см. `requirements.txt`.

## Проверки

- `python3 -m compileall -q -x '(^|/)(venv|\.git|__pycache__)(/|$)' .` — OK.
- `python3 -m json.tool database.json > /dev/null` — OK.
- Полная сборка `python3 main.py` в этой сессии не запускалась: перед релизом
  или изменением `builder.py`/`formatter.py` прогнать и проверить XML Excel
  (см. «Проверка Excel» в `AGENTS.md`).

## Что сделано в этой сессии

- `AGENTS.md`: добавлен раздел про `compileall` и ограничения проверки.
- `docs/GIT_WORKFLOW.md`: процесс доведён до production-grade (sync/rebase,
  diff, бэкапы, `--ff-only`/`--no-ff`, конфликты данных, changelog, откат,
  чек-лист). Документ объявлен источником истины по git-процессу.
- `database.json`: документ «Доп. соглашение №1» перенесён из `documents`
  в `documents_archived` (подобъект `01_271_КН`).
- Удалена устаревшая remote-ветка `fix/bug-hotfix` (её коммиты уже были в `main`).
- Добавлены `docs/HANDOFF.md`, `docs/DECISIONS.md`, `requirements.txt`.

## Следующие шаги

1. Проверить открытые пункты `TODO.md`: A3/A4 (затирание статусов), C1/C2
   (доп. соглашения и обозначения договоров).
2. Устранить расхождение: `main.py` строит из `config.DATA_ROWS`, хотя
   источник данных — `database.json`. Решить, что считать истиной, и
   синхронизировать путь сборки.
3. Удалить или явно пометить дубль `wizard_edits_new.py`.
4. Добавить автотесты (`pytest`) на фикстуре копии `database.json`.
5. Ввести `ruff`/`black`, атомарную запись БД, разбить `builder.py`.

## Открытые вопросы и риски

- `builder.py` (568 строк) — высокая связность, риск регрессий при правках.
- Нет автоматических тестов; проверка ручная.
- `storage.py` содержит `except Exception: pass` — ошибки чтения истории
  могут скрываться.
- `database.json` — рабочая база; перед экспериментами делать бэкап.
- `*.xlsx` в `.gitignore`, но физически лежат в папке проекта.

## Как воспроизвести

```bash
python3 -m pip install -r requirements.txt
python3 -m compileall -q -x '(^|/)(venv|\.git|__pycache__)(/|$)' .
python3 main.py
```

Результат: `Трекер_Акт_Выполнения.xlsx` и `Документы_Подобъектов.xlsx`
(если в БД есть архивированные документы).
