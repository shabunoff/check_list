from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Импорт чек-листа отключен. Чек-листы создаются только вручную через интерфейс.'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)
        parser.add_argument('--title', type=str, default=None)

    def handle(self, *args, **options):
        raise CommandError('Импорт чек-листа отключен. Создавайте чек-листы вручную в разделе /checklists.')
