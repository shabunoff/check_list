# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Checklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активный')),
            ],
            options={
                'verbose_name': 'Чек-лист',
                'verbose_name_plural': 'Чек-листы',
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Executor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=255, verbose_name='ФИО')),
                ('city', models.CharField(max_length=255, verbose_name='Город/филиал')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активный')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'Сотрудник',
                'verbose_name_plural': 'Сотрудники',
                'ordering': ['full_name'],
            },
        ),
        migrations.CreateModel(
            name='ChecklistSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Раздел')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='audits.checklist', verbose_name='Чек-лист')),
            ],
            options={
                'verbose_name': 'Раздел чек-листа',
                'verbose_name_plural': 'Разделы чек-листа',
                'ordering': ['checklist', 'order', 'id'],
                'unique_together': {('checklist', 'title')},
            },
        ),
        migrations.CreateModel(
            name='ChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Пункт')),
                ('importance', models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3')], verbose_name='Важность')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='audits.checklistsection', verbose_name='Раздел')),
            ],
            options={
                'verbose_name': 'Пункт чек-листа',
                'verbose_name_plural': 'Пункты чек-листа',
                'ordering': ['section', 'order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Audit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('completed', 'Завершен')], default='draft', max_length=16, verbose_name='Статус')),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='audits', to='audits.checklist', verbose_name='Чек-лист')),
                ('executor', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='audit', to='audits.executor', verbose_name='Сотрудник')),
            ],
            options={
                'verbose_name': 'Аудит',
                'verbose_name_plural': 'Аудиты',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AuditAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_note', models.TextField(blank=True, default='')),
                ('compliance', models.CharField(blank=True, choices=[('Да', 'Да'), ('Нет', 'Нет'), ('Частично', 'Частично')], default='', max_length=20)),
                ('actual_behavior', models.TextField(blank=True, default='')),
                ('deviation', models.TextField(blank=True, default='')),
                ('violation_type', models.CharField(blank=True, choices=[('Фин', 'Фин'), ('Тех', 'Тех'), ('Рег', 'Рег')], default='', max_length=10)),
                ('ready_to_accept', models.CharField(blank=True, choices=[('Да', 'Да'), ('При условиях', 'При условиях'), ('Нет', 'Нет')], default='', max_length=20)),
                ('comment', models.TextField(blank=True, default='')),
                ('audit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='audits.audit')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='answers', to='audits.checklistitem')),
            ],
            options={
                'verbose_name': 'Ответ аудита',
                'verbose_name_plural': 'Ответы аудита',
                'ordering': ['item__section__order', 'item__order', 'id'],
                'unique_together': {('audit', 'item')},
            },
        ),
    ]
