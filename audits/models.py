from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Executor(models.Model):
    full_name = models.CharField(max_length=255, verbose_name='ФИО')
    city = models.CharField(max_length=255, verbose_name='Группа')
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Респондент'
        verbose_name_plural = 'Респонденты'

    def __str__(self):
        return self.full_name


class Checklist(models.Model):
    title = models.CharField(max_length=255, unique=True, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активный')

    class Meta:
        ordering = ['title']
        verbose_name = 'Чек-лист'
        verbose_name_plural = 'Чек-листы'

    def __str__(self):
        return self.title


class ChecklistSection(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='sections', verbose_name='Чек-лист')
    title = models.CharField(max_length=255, verbose_name='Раздел')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['checklist', 'order', 'id']
        verbose_name = 'Раздел чек-листа'
        verbose_name_plural = 'Разделы чек-листа'

    def __str__(self):
        return f'{self.checklist}: {self.title}'


class ChecklistItem(models.Model):
    section = models.ForeignKey(ChecklistSection, on_delete=models.CASCADE, related_name='items', verbose_name='Раздел')
    text = models.TextField(verbose_name='Пункт')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['section', 'order', 'id']
        verbose_name = 'Пункт чек-листа'
        verbose_name_plural = 'Пункты чек-листа'

    def __str__(self):
        return self.text[:80]


class ChecklistField(models.Model):
    TYPE_TEXT = 'text'
    TYPE_NUMBER = 'number'
    TYPE_SELECT = 'select'
    TYPE_CHOICES = (
        (TYPE_TEXT, 'Текст'),
        (TYPE_NUMBER, 'Число'),
        (TYPE_SELECT, 'Выбор из списка'),
    )

    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='fields', verbose_name='Пункт')
    title = models.CharField(max_length=255, verbose_name='Название поля')
    field_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Тип поля')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['item', 'order', 'id']
        verbose_name = 'Поле пункта чек-листа'
        verbose_name_plural = 'Поля пунктов чек-листа'

    def __str__(self):
        return f'{self.item_id} - {self.title}'


class ChecklistFieldOption(models.Model):
    field = models.ForeignKey(ChecklistField, on_delete=models.CASCADE, related_name='options', verbose_name='Поле')
    value = models.CharField(max_length=255, verbose_name='Значение')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['field', 'order', 'id']
        verbose_name = 'Опция поля'
        verbose_name_plural = 'Опции полей'

    def __str__(self):
        return self.value


class Audit(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_COMPLETED, 'Завершен'),
    )

    executor = models.ForeignKey(Executor, on_delete=models.PROTECT, related_name='audits', verbose_name='Респондент')
    checklist = models.ForeignKey(Checklist, on_delete=models.PROTECT, related_name='audits', verbose_name='Чек-лист')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT, verbose_name='Статус')

    class Meta:
        ordering = ['-created_at']
        unique_together = ('executor', 'checklist')
        verbose_name = 'Аудит'
        verbose_name_plural = 'Аудиты'

    def __str__(self):
        return f'Аудит: {self.executor.full_name} / {self.checklist.title}'


class ChecklistAssignment(models.Model):
    STATUS_ASSIGNED = 'assigned'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = (
        (STATUS_ASSIGNED, 'Назначен'),
        (STATUS_IN_PROGRESS, 'В работе'),
        (STATUS_COMPLETED, 'Завершен'),
    )

    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='assignments', verbose_name='Чек-лист')
    executor = models.ForeignKey(Executor, on_delete=models.CASCADE, related_name='assignments', verbose_name='Респондент')
    manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='checklist_assignments', verbose_name='Менеджер')
    audit = models.ForeignKey(Audit, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments', verbose_name='Аудит')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ASSIGNED, verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        ordering = ['-created_at']
        unique_together = ('checklist', 'executor')
        verbose_name = 'Назначение на опрос'
        verbose_name_plural = 'Назначения на опрос'

    def __str__(self):
        return f'{self.checklist.title} / {self.executor.full_name} / {self.manager}'


class AuditFieldValue(models.Model):
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='values', verbose_name='Аудит')
    field = models.ForeignKey(ChecklistField, on_delete=models.PROTECT, related_name='values', verbose_name='Поле')
    value = models.TextField(blank=True, default='', verbose_name='Значение')

    class Meta:
        unique_together = ('audit', 'field')
        ordering = ['field__item__section__order', 'field__item__order', 'field__order', 'id']
        verbose_name = 'Значение поля аудита'
        verbose_name_plural = 'Значения полей аудита'

    def __str__(self):
        return f'{self.audit_id}:{self.field_id}'

