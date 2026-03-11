from django.contrib import admin

from .models import (
    Audit,
    AuditFieldValue,
    Checklist,
    ChecklistAssignment,
    ChecklistField,
    ChecklistFieldOption,
    ChecklistItem,
    ChecklistSection,
    Executor,
)


class ChecklistFieldOptionInline(admin.TabularInline):
    model = ChecklistFieldOption
    extra = 0


class ChecklistFieldInline(admin.TabularInline):
    model = ChecklistField
    extra = 0


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0


@admin.register(Executor)
class ExecutorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'city', 'is_active', 'created_at')
    list_filter = ('city', 'is_active')
    search_fields = ('full_name', 'city')


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)


@admin.register(ChecklistSection)
class ChecklistSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'checklist', 'order')
    list_filter = ('checklist',)
    inlines = [ChecklistItemInline]


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('text', 'section', 'order')
    list_filter = ('section__checklist',)
    search_fields = ('text',)
    inlines = [ChecklistFieldInline]


@admin.register(ChecklistField)
class ChecklistFieldAdmin(admin.ModelAdmin):
    list_display = ('title', 'item', 'field_type', 'order')
    list_filter = ('field_type', 'item__section__checklist')
    search_fields = ('title', 'item__text')
    inlines = [ChecklistFieldOptionInline]


@admin.register(ChecklistFieldOption)
class ChecklistFieldOptionAdmin(admin.ModelAdmin):
    list_display = ('value', 'field', 'order')
    list_filter = ('field__item__section__checklist',)


@admin.register(ChecklistAssignment)
class ChecklistAssignmentAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'executor', 'manager', 'status', 'audit', 'created_at')
    list_filter = ('checklist', 'manager', 'status')
    search_fields = ('executor__full_name', 'manager__username', 'checklist__title')


class AuditFieldValueInline(admin.TabularInline):
    model = AuditFieldValue
    extra = 0


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('executor', 'checklist', 'status', 'created_at')
    list_filter = ('status', 'checklist')
    search_fields = ('executor__full_name',)
    inlines = [AuditFieldValueInline]
