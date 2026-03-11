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
python manage.py runserver 0.0.0.0:8000
```

Важно:
- Для доступа с других устройств в сети запускать на `0.0.0.0:8000`.
- Для корректной загрузки лого/favicon используется `STATICFILES_DIRS = [BASE_DIR / 'static']`.

## 2) Первичная настройка
1. Войти в `/admin`.
2. Создать пользователей.
3. Назначить группы:
   - `leader`
   - `manager`
4. Импортировать респондентов (`/executors/import`).
5. Создать чек-лист вручную (`/checklists`).

## 3) Ручной конструктор чек-листа
1. `/checklists` -> создать чек-лист.
2. `/checklists/<id>`:
   - добавить разделы;
   - добавить пункты;
   - добавить поля (`text/number/select`);
   - добавить опции для `select`.

## 4) Назначения респондентов на опрос
Только `leader`, страница `/checklists/<id>`:
1. Выбрать менеджера.
2. Отметить респондентов чекбоксами.
3. Можно нажать `Выбрать всех`, затем снять выбор у нужных.
4. Нажать `Назначить выбранных`.

## 5) Работа менеджера
1. `/survey` -> список его чек-листов с назначениями.
2. `/checklists/<id>/survey` -> список респондентов к опросу.
3. Фильтровать список:
   - по респонденту;
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
### Импорт респондентов
```powershell
python manage.py import_executors C:\path\respondents.xlsx
```
Формат Excel: `ФИО | Группа`.

### Экспорт
- `/reports/export/matrix`
- `/reports/export/rows`
- `/checklists/<id>/export-min`
- `/checklists/<id>/export-answers`

## 9) Ребрендинг
- Продукт: `CheckList+`.
- Лого: `static/img/logo2.svg`.
- Favicon: `static/img/favicon.svg`.
- Футтер: разработчик `Shabunoff Systems Lab` + ссылка `https://shabunoff.ru/`.

## 10) Проверка после обновлений
```powershell
python manage.py check
python manage.py migrate
```

Smoke-check:
- `/login` (лого + favicon);
- `/checklists` (динамика, проценты, прогресс);
- `/checklists/<id>/survey` (фильтры);
- экспорты `export-min` и `export-answers`;
- удаление чек-листа на `/checklists`.
