# Operations Guide

Дата актуализации: 2026-03-11

## 1) Локальный запуск
```powershell
cd C:\vibe_code\dez_audit\audit_project
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 2) Первичная настройка
1. Войти в `/admin`.
2. Создать пользователей.
3. Назначить группы:
   - `leader`
   - `manager`
4. Импортировать сотрудников (`/executors/import`).
5. Создать чек-лист вручную (`/checklists`).

## 3) Ручной конструктор чек-листа
1. `/checklists` -> создать чек-лист.
2. `/checklists/<id>`:
   - добавить разделы;
   - добавить пункты;
   - добавить поля (`text/number/select`);
   - добавить опции для `select`.

## 4) Назначения сотрудников на опрос
Только `leader`, страница `/checklists/<id>`:
1. Выбрать менеджера.
2. Отметить сотрудников чекбоксами.
3. Можно нажать `Выбрать всех`, затем снять выбор у нужных.
4. Нажать `Назначить выбранных`.

## 5) Работа менеджера
1. `/survey` -> список его чек-листов с назначениями.
2. `/checklists/<id>/survey` -> список сотрудников к опросу.
3. Фильтровать список:
   - по сотруднику;
   - по статусу (`Не создан`, `Черновик`, `Завершен`).
4. Действия по строке:
   - `Начать` (аудит еще не создан);
   - `Открыть` (черновик);
   - `Изменить` (завершенный аудит).
5. Заполнить аудит на `/audit/<id>`.

## 6) Доступ к `/checklists`
- `leader`: страница управления чек-листами.
- `manager`: редирект на `/survey`.

## 7) Удаление чек-листа
На `/checklists` (только `leader`) доступна кнопка `Удалить`.

Удаляется полностью:
- чек-лист;
- разделы, пункты, поля, опции;
- назначения (`ChecklistAssignment`);
- аудиты по чек-листу (`Audit`);
- ответы аудитов (`AuditFieldValue`).

Операция необратима.

## 8) Импорт/экспорт
### Импорт сотрудников
```powershell
python manage.py import_executors C:\path\executors.xlsx
```

### Экспорт
- `/reports/export/matrix`
- `/reports/export/rows`
- `/checklists/<id>/export-min`
- `/checklists/<id>/export-answers`

## 9) Проверка после обновлений
```powershell
python manage.py check
python manage.py migrate
```

Smoke-check:
- массовое назначение в `/checklists/<id>`;
- запуск аудита из `/checklists/<id>/survey`;
- фильтры в `/checklists/<id>/survey`;
- экспорты `export-min` и `export-answers`;
- удаление чек-листа на `/checklists`.
