# Generated manually: checklist assignments for manager interviews.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('audits', '0003_multi_audit_per_executor'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChecklistAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('assigned', 'Назначен'), ('in_progress', 'В работе'), ('completed', 'Завершен')], default='assigned', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('audit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assignments', to='audits.audit', verbose_name='Аудит')),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='audits.checklist', verbose_name='Чек-лист')),
                ('executor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='audits.executor', verbose_name='Сотрудник')),
                ('manager', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checklist_assignments', to=settings.AUTH_USER_MODEL, verbose_name='Менеджер')),
            ],
            options={
                'verbose_name': 'Назначение на опрос',
                'verbose_name_plural': 'Назначения на опрос',
                'ordering': ['-created_at'],
                'unique_together': {('checklist', 'executor')},
            },
        ),
    ]
