from django import forms
from django.contrib.auth import get_user_model

from .models import (
    Audit,
    Checklist,
    ChecklistAssignment,
    ChecklistField,
    ChecklistFieldOption,
    ChecklistItem,
    ChecklistSection,
    Executor,
)

User = get_user_model()


class ExecutorForm(forms.ModelForm):
    class Meta:
        model = Executor
        fields = ['full_name', 'city', 'is_active']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ExcelUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))


class AuditStatusForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm w-auto'}),
        }


class StartAuditForm(forms.Form):
    checklist = forms.ModelChoiceField(
        queryset=Checklist.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['checklist'].queryset = Checklist.objects.filter(is_active=True).order_by('title')


class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['title', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ChecklistSectionForm(forms.ModelForm):
    class Meta:
        model = ChecklistSection
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }


class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ['text', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 2}),
            'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }


class ChecklistFieldForm(forms.ModelForm):
    class Meta:
        model = ChecklistField
        fields = ['title', 'field_type', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'field_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }


class ChecklistFieldOptionForm(forms.ModelForm):
    class Meta:
        model = ChecklistFieldOption
        fields = ['value', 'order']
        widgets = {
            'value': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }


class ChecklistAssignmentForm(forms.ModelForm):
    class Meta:
        model = ChecklistAssignment
        fields = ['executor', 'manager']
        widgets = {
            'executor': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'manager': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }

    def __init__(self, *args, checklist=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['executor'].queryset = Executor.objects.filter(is_active=True).order_by('full_name')

        manager_group_users = User.objects.filter(groups__name='manager')
        leader_group_users = User.objects.filter(groups__name='leader')
        self.fields['manager'].queryset = (manager_group_users | leader_group_users | User.objects.filter(is_superuser=True)).distinct().order_by('username')

        if checklist is not None:
            assigned_executor_ids = checklist.assignments.values_list('executor_id', flat=True)
            self.fields['executor'].queryset = self.fields['executor'].queryset.exclude(id__in=assigned_executor_ids)
