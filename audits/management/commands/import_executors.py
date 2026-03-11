from django.core.management.base import BaseCommand, CommandError

from audits.services import ImportErrorMessage, import_executors_from_workbook


class Command(BaseCommand):
    help = 'Импорт респондентов из Excel (ФИО | Группа)'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)

    def handle(self, *args, **options):
        path = options['file']
        try:
            with open(path, 'rb') as f:
                result = import_executors_from_workbook(f)
        except FileNotFoundError as exc:
            raise CommandError(f'Файл не найден: {path}') from exc
        except ImportErrorMessage as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(
            f"Импорт завершен. Добавлено: {result['created']}, обновлено: {result['updated']}"
        ))

