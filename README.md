# Dez Audit (Django 5)

Простое веб-приложение для аудита сотрудников по ручным чек-листам с назначениями на опрос.

## Стек
- Python 3.12
- Django 5
- SQLite
- Django Templates + Bootstrap 5 (CDN)
- openpyxl

## Установка
```bash
cd audit_project
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
```

## Запуск
```bash
python manage.py runserver
```

## Основные URL
- `/login`
- `/executors`
- `/checklists`
- `/survey`
- `/reports`
- `/admin`

## Пользователи и роли
Создайте superuser:
```bash
python manage.py createsuperuser
```

Через admin добавьте пользователей в группы:
- `manager` - проводит опросы и заполняет аудиты.
- `leader` - управляет чек-листами, назначениями, экспортами.

## Чек-листы (только вручную)
Импорт чек-листов отключен.

Конструктор:
1. `/checklists` -> создать чек-лист.
2. `/checklists/<id>` -> добавить разделы, пункты, поля (`text|number|select`), опции для `select`.

## Назначения на опрос
В `/checklists/<id>` (leader):
- выбрать менеджера;
- выбрать сотрудников чекбоксами;
- поддержаны действия `Выбрать всех` и снятие выбора у отдельных сотрудников;
- нажать `Назначить выбранных`.

Менеджер работает через:
- `/survey` (список назначенных чек-листов)
- `/checklists/<id>/survey` (сотрудники к опросу, запуск/открытие аудита)

## Импорт сотрудников
Формат Excel: `ФИО | Город`

Команда:
```bash
python manage.py import_executors C:\path\executors.xlsx
```

UI:
- `/executors/import`

## Аудиты
- У сотрудника может быть несколько аудитов по разным чек-листам.
- На одного сотрудника и один чек-лист допускается только один аудит (`executor + checklist` уникальны).
- Статусы: `draft`, `completed`.
- Поля аудита сохраняются автоматически (AJAX).

## Экспорты
- `/reports/export/matrix`
- `/reports/export/rows`
- `/checklists/<id>/export-min` (минимальный экспорт по конкретному чек-листу)

## Документация
- `docs/README.md`
- `docs/PROJECT_STATUS.md`
- `docs/OPERATIONS.md`
- `docs/CHANGELOG.md`
