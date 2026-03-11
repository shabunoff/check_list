# Generated manually for checklist constructor redesign.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('audits', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='checklistsection',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='checklistitem',
            name='importance',
        ),
        migrations.CreateModel(
            name='ChecklistField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название поля')),
                ('field_type', models.CharField(choices=[('text', 'Текст'), ('number', 'Число'), ('select', 'Выбор из списка')], max_length=20, verbose_name='Тип поля')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='audits.checklistitem', verbose_name='Пункт')),
            ],
            options={
                'verbose_name': 'Поле пункта чек-листа',
                'verbose_name_plural': 'Поля пунктов чек-листа',
                'ordering': ['item', 'order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ChecklistFieldOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, verbose_name='Значение')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='audits.checklistfield', verbose_name='Поле')),
            ],
            options={
                'verbose_name': 'Опция поля',
                'verbose_name_plural': 'Опции полей',
                'ordering': ['field', 'order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AuditFieldValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField(blank=True, default='', verbose_name='Значение')),
                ('audit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='audits.audit', verbose_name='Аудит')),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='values', to='audits.checklistfield', verbose_name='Поле')),
            ],
            options={
                'verbose_name': 'Значение поля аудита',
                'verbose_name_plural': 'Значения полей аудита',
                'ordering': ['field__item__section__order', 'field__item__order', 'field__order', 'id'],
                'unique_together': {('audit', 'field')},
            },
        ),
        migrations.DeleteModel(
            name='AuditAnswer',
        ),
    ]
