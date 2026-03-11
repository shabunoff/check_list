# Generated manually: allow multiple audits per executor for different checklists.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('audits', '0002_dynamic_checklist_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audit',
            name='executor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='audits', to='audits.executor', verbose_name='Сотрудник'),
        ),
        migrations.AlterUniqueTogether(
            name='audit',
            unique_together={('executor', 'checklist')},
        ),
    ]
