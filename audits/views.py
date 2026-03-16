from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.db.transaction import atomic
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AuditStatusForm,
    ChecklistFieldForm,
    ChecklistFieldOptionForm,
    ChecklistForm,
    ChecklistItemForm,
    ChecklistSectionForm,
    ExcelUploadForm,
    ExecutorForm,
    StartAuditForm,
)
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
from .permissions import ensure_leader, is_leader, manager_required
from .services import (
    ImportErrorMessage,
    build_checklist_answers_export_workbook,
    build_checklist_assignments_export_workbook,
    build_export_matrix_workbook,
    build_export_rows_workbook,
    import_executors_from_workbook,
)


User = get_user_model()

@login_required
def home_redirect(request):
    return redirect('executors_list')


@manager_required
def executors_list(request):
    can_manage = is_leader(request.user)

    if request.method == 'POST':
        ensure_leader(request.user)
        action = request.POST.get('action')

        if action == 'add_executor':
            add_form = ExecutorForm(request.POST)
            if add_form.is_valid():
                add_form.save()
                messages.success(request, 'Респондент добавлен')
                return redirect('executors_list')

        elif action == 'bulk_deactivate':
            selected_ids = request.POST.getlist('executor_ids')
            if not selected_ids:
                messages.warning(request, 'Выберите респондентов для группового удаления')
                return redirect('executors_list')

            updated_count = Executor.objects.filter(id__in=selected_ids, is_active=True).update(is_active=False)
            messages.success(request, f'Деактивировано респондентов: {updated_count}')
            return redirect('executors_list')

        elif action == 'bulk_hard_delete':
            selected_ids = request.POST.getlist('executor_ids')
            if not selected_ids:
                messages.warning(request, 'Выберите респондентов для полного удаления')
                return redirect('executors_list')

            with atomic():
                audits_qs = Audit.objects.filter(executor_id__in=selected_ids)
                AuditFieldValue.objects.filter(audit__in=audits_qs).delete()
                audits_qs.delete()
                deleted_count, _ = Executor.objects.filter(id__in=selected_ids).delete()

            messages.success(request, f'Полностью удалено записей респондентов: {deleted_count}')
            return redirect('executors_list')

        else:
            add_form = ExecutorForm(initial={'is_active': True})
    else:
        add_form = ExecutorForm(initial={'is_active': True})

    city = request.GET.get('city', '').strip()
    executors = Executor.objects.all().annotate(has_audit=Count('audits'))
    if city:
        executors = executors.filter(city=city)

    cities = Executor.objects.values_list('city', flat=True).distinct().order_by('city')

    return render(
        request,
        'audits/executors_list.html',
        {
            'executors': executors,
            'cities': cities,
            'selected_city': city,
            'can_manage': can_manage,
            'add_form': add_form,
        },
    )


@manager_required
def executor_detail(request, executor_id):
    executor = get_object_or_404(Executor, pk=executor_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_executor':
            ensure_leader(request.user)
            form = ExecutorForm(request.POST, instance=executor)
            if form.is_valid():
                form.save()
                messages.success(request, 'Респондент сохранен')
                return redirect('executor_detail', executor_id=executor.id)

        elif action == 'start_audit':
            if not executor.is_active:
                messages.error(request, 'Нельзя создать аудит для неактивного респондента')
                return redirect('executor_detail', executor_id=executor.id)

            start_form = StartAuditForm(request.POST)
            if start_form.is_valid():
                checklist = start_form.cleaned_data['checklist']
                audit, created = Audit.objects.get_or_create(executor=executor, checklist=checklist)
                if created:
                    messages.success(request, 'Аудит создан')
                else:
                    messages.info(request, 'Аудит для этого чек-листа уже существует, открыт существующий')
                return redirect('audit_detail', audit_id=audit.id)

        elif action == 'toggle_active':
            ensure_leader(request.user)
            executor.is_active = not executor.is_active
            executor.save(update_fields=['is_active'])
            messages.success(request, 'Статус респондента обновлен')
            return redirect('executor_detail', executor_id=executor.id)

    form = ExecutorForm(instance=executor)
    start_form = StartAuditForm()

    audits = Audit.objects.filter(executor=executor).select_related('checklist').order_by('-created_at')
    used_checklist_ids = set(audits.values_list('checklist_id', flat=True))
    available_checklists = Checklist.objects.filter(is_active=True).exclude(id__in=used_checklist_ids).order_by('title')
    start_form.fields['checklist'].queryset = available_checklists

    return render(
        request,
        'audits/executor_detail.html',
        {
            'executor': executor,
            'audits': audits,
            'form': form,
            'start_form': start_form,
            'can_manage': is_leader(request.user),
            'has_available_checklists': available_checklists.exists(),
        },
    )


@manager_required
def executors_import(request):
    ensure_leader(request.user)

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = import_executors_from_workbook(form.cleaned_data['file'])
            except ImportErrorMessage as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Импорт завершен. Добавлено: {result['created']}, обновлено: {result['updated']}",
                )
                return redirect('executors_list')
    else:
        form = ExcelUploadForm()

    return render(request, 'audits/import_excel.html', {'form': form, 'title': 'Импорт респондентов'})


@manager_required
def checklists_page(request):
    if not is_leader(request.user):
        return redirect('survey_list')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_checklist':
            form = ChecklistForm(request.POST)
            if form.is_valid():
                checklist = form.save()
                messages.success(request, 'Чек-лист создан')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'toggle_active':
            checklist = get_object_or_404(Checklist, pk=request.POST.get('checklist_id'))
            checklist.is_active = not checklist.is_active
            checklist.save(update_fields=['is_active'])
            messages.success(request, 'Статус чек-листа обновлен')
            return redirect('checklists_page')

        elif action == 'delete_checklist':
            checklist = get_object_or_404(Checklist, pk=request.POST.get('checklist_id'))
            checklist_title = checklist.title

            with atomic():
                audits_qs = Audit.objects.filter(checklist=checklist)
                AuditFieldValue.objects.filter(audit__in=audits_qs).delete()
                ChecklistAssignment.objects.filter(checklist=checklist).delete()
                audits_qs.delete()
                checklist.delete()

            messages.success(request, f'Чек-лист "{checklist_title}" удален полностью')
            return redirect('checklists_page')

        else:
            form = ChecklistForm(initial={'is_active': True})
    else:
        form = ChecklistForm(initial={'is_active': True})

    checklists = Checklist.objects.annotate(
        sections_count=Count('sections', distinct=True),
        items_count=Count('sections__items', distinct=True),
        fields_count=Count('sections__items__fields', distinct=True),
        assignments_count=Count('assignments', distinct=True),
        completed_count=Count(
            'assignments',
            filter=Q(assignments__audit__status=Audit.STATUS_COMPLETED),
            distinct=True,
        ),
        draft_count=Count(
            'assignments',
            filter=Q(assignments__audit__status=Audit.STATUS_DRAFT),
            distinct=True,
        ),
        not_started_count=Count(
            'assignments',
            filter=Q(assignments__audit__isnull=True),
            distinct=True,
        ),
    ).order_by('title')

    for checklist in checklists:
        total = checklist.assignments_count or 0
        checklist.completed_percent = int((checklist.completed_count * 100) / total) if total else 0
        checklist.draft_percent = int((checklist.draft_count * 100) / total) if total else 0
        checklist.not_started_percent = int((checklist.not_started_count * 100) / total) if total else 0

    return render(
        request,
        'audits/checklists.html',
        {
            'checklists': checklists,
            'form': form,
        },
    )


@manager_required
def checklist_detail(request, checklist_id):
    ensure_leader(request.user)

    checklist = get_object_or_404(Checklist.objects.prefetch_related('sections__items__fields__options'), pk=checklist_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_section':
            section_form = ChecklistSectionForm(request.POST)
            if section_form.is_valid():
                section = section_form.save(commit=False)
                section.checklist = checklist
                section.save()
                messages.success(request, 'Раздел добавлен')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'edit_section':
            section = get_object_or_404(ChecklistSection, pk=request.POST.get('section_id'), checklist=checklist)
            section_form = ChecklistSectionForm(request.POST, instance=section)
            if section_form.is_valid():
                section_form.save()
                messages.success(request, 'Раздел обновлен')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'copy_section':
            source_section = get_object_or_404(ChecklistSection, pk=request.POST.get('section_id'), checklist=checklist)
            with atomic():
                next_order = (checklist.sections.aggregate(max_order=Max('order')).get('max_order') or 0) + 10
                new_section = ChecklistSection.objects.create(
                    checklist=checklist,
                    title=f'{source_section.title} (копия)',
                    order=next_order,
                )

                for src_item in source_section.items.prefetch_related('fields__options').all().order_by('order', 'id'):
                    new_item = ChecklistItem.objects.create(
                        section=new_section,
                        text=src_item.text,
                        order=src_item.order,
                    )
                    for src_field in src_item.fields.all().order_by('order', 'id'):
                        new_field = ChecklistField.objects.create(
                            item=new_item,
                            title=src_field.title,
                            field_type=src_field.field_type,
                            order=src_field.order,
                        )
                        for src_option in src_field.options.all().order_by('order', 'id'):
                            ChecklistFieldOption.objects.create(
                                field=new_field,
                                value=src_option.value,
                                order=src_option.order,
                            )

            messages.success(request, 'Раздел скопирован вместе с пунктами и полями')
            return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'add_item':
            section = get_object_or_404(ChecklistSection, pk=request.POST.get('section_id'), checklist=checklist)
            item_form = ChecklistItemForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.section = section
                item.save()
                messages.success(request, 'Пункт добавлен')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'edit_item':
            item = get_object_or_404(ChecklistItem, pk=request.POST.get('item_id'), section__checklist=checklist)
            item_form = ChecklistItemForm(request.POST, instance=item)
            if item_form.is_valid():
                item_form.save()
                messages.success(request, 'Пункт обновлен')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'copy_item':
            source_item = get_object_or_404(ChecklistItem, pk=request.POST.get('item_id'), section__checklist=checklist)
            target_section = get_object_or_404(ChecklistSection, pk=request.POST.get('target_section_id'), checklist=checklist)

            with atomic():
                next_order = (target_section.items.aggregate(max_order=Max('order')).get('max_order') or 0) + 10
                new_item = ChecklistItem.objects.create(
                    section=target_section,
                    text=f'{source_item.text} (копия)',
                    order=next_order,
                )

                for src_field in source_item.fields.prefetch_related('options').all().order_by('order', 'id'):
                    new_field = ChecklistField.objects.create(
                        item=new_item,
                        title=src_field.title,
                        field_type=src_field.field_type,
                        order=src_field.order,
                    )
                    for src_option in src_field.options.all().order_by('order', 'id'):
                        ChecklistFieldOption.objects.create(
                            field=new_field,
                            value=src_option.value,
                            order=src_option.order,
                        )

            messages.success(request, 'Пункт скопирован вместе с полями')
            return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'add_field':
            item = get_object_or_404(ChecklistItem, pk=request.POST.get('item_id'), section__checklist=checklist)
            field_form = ChecklistFieldForm(request.POST)
            if field_form.is_valid():
                field = field_form.save(commit=False)
                field.item = item
                field.save()
                messages.success(request, 'Поле добавлено')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'edit_field':
            field = get_object_or_404(ChecklistField, pk=request.POST.get('field_id'), item__section__checklist=checklist)
            field_form = ChecklistFieldForm(request.POST, instance=field)
            if field_form.is_valid():
                field_form.save()
                messages.success(request, 'Поле обновлено')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'add_option':
            field = get_object_or_404(ChecklistField, pk=request.POST.get('field_id'), item__section__checklist=checklist)
            if field.field_type != ChecklistField.TYPE_SELECT:
                messages.error(request, 'Опции доступны только для типа "Выбор из списка"')
                return redirect('checklist_detail', checklist_id=checklist.id)

            option_form = ChecklistFieldOptionForm(request.POST)
            if option_form.is_valid():
                opt = option_form.save(commit=False)
                opt.field = field
                opt.save()
                messages.success(request, 'Опция добавлена')
                return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'add_assignments_bulk':
            manager_id = request.POST.get('manager_id')
            selected_executor_ids = request.POST.getlist('executor_ids')

            manager_group_users = User.objects.filter(groups__name='manager')
            leader_group_users = User.objects.filter(groups__name='leader')
            managers_qs = (manager_group_users | leader_group_users | User.objects.filter(is_superuser=True)).distinct()

            if not manager_id:
                messages.error(request, 'Выберите менеджера для назначения')
                return redirect('checklist_detail', checklist_id=checklist.id)

            manager = managers_qs.filter(id=manager_id).first()
            if manager is None:
                messages.error(request, 'Выбран недопустимый менеджер')
                return redirect('checklist_detail', checklist_id=checklist.id)

            if not selected_executor_ids:
                messages.warning(request, 'Выберите хотя бы одного респондента')
                return redirect('checklist_detail', checklist_id=checklist.id)

            created_count = 0
            for executor in Executor.objects.filter(id__in=selected_executor_ids, is_active=True):
                _, created = ChecklistAssignment.objects.get_or_create(
                    checklist=checklist,
                    executor=executor,
                    defaults={'manager': manager},
                )
                if created:
                    created_count += 1

            messages.success(request, f'Назначений создано: {created_count}')
            return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'delete_assignment':
            assignment = get_object_or_404(ChecklistAssignment, pk=request.POST.get('assignment_id'), checklist=checklist)
            assignment.delete()
            messages.success(request, 'Назначение удалено')
            return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'delete_section':
            section = get_object_or_404(ChecklistSection, pk=request.POST.get('section_id'), checklist=checklist)
            section.delete()
            messages.success(request, 'Раздел удален')
            return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'delete_item':
            item = get_object_or_404(ChecklistItem, pk=request.POST.get('item_id'), section__checklist=checklist)
            item.delete()
            messages.success(request, 'Пункт удален')
            return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'delete_field':
            field = get_object_or_404(ChecklistField, pk=request.POST.get('field_id'), item__section__checklist=checklist)
            field.delete()
            messages.success(request, 'Поле удалено')
            return redirect('checklist_detail', checklist_id=checklist.id)

        elif action == 'delete_option':
            option = get_object_or_404(ChecklistFieldOption, pk=request.POST.get('option_id'), field__item__section__checklist=checklist)
            option.delete()
            messages.success(request, 'Опция удалена')
            return redirect('checklist_detail', checklist_id=checklist.id)

    sections = checklist.sections.all().order_by('order', 'id')
    assignments = checklist.assignments.select_related('executor', 'manager', 'audit').order_by('executor__full_name')
    assigned_executor_ids = assignments.values_list('executor_id', flat=True)
    available_executors = Executor.objects.filter(is_active=True).exclude(id__in=assigned_executor_ids).order_by('full_name')

    manager_group_users = User.objects.filter(groups__name='manager')
    leader_group_users = User.objects.filter(groups__name='leader')
    managers = (manager_group_users | leader_group_users | User.objects.filter(is_superuser=True)).distinct().order_by('username')

    return render(
        request,
        'audits/checklist_detail.html',
        {
            'checklist': checklist,
            'sections': sections,
            'assignments': assignments,
            'available_executors': available_executors,
            'managers': managers,
            'field_type_choices': ChecklistField.TYPE_CHOICES,
            'section_form': ChecklistSectionForm(initial={'order': 10}),
            'item_form': ChecklistItemForm(initial={'order': 10}),
            'field_form': ChecklistFieldForm(initial={'order': 10, 'field_type': ChecklistField.TYPE_TEXT}),
            'option_form': ChecklistFieldOptionForm(initial={'order': 10}),
        },
    )


@manager_required
def survey_list(request):
    assignments = ChecklistAssignment.objects.filter(manager=request.user).select_related('checklist')

    checklist_ids = assignments.values_list('checklist_id', flat=True).distinct()
    checklists = Checklist.objects.filter(id__in=checklist_ids).annotate(
        total_assigned=Count('assignments', filter=Q(assignments__manager=request.user), distinct=True),
        completed_assigned=Count('assignments', filter=Q(assignments__manager=request.user, assignments__status=ChecklistAssignment.STATUS_COMPLETED), distinct=True),
    ).order_by('title')

    return render(request, 'audits/survey_list.html', {'checklists': checklists})


@manager_required
def checklist_survey(request, checklist_id):
    checklist = get_object_or_404(Checklist, pk=checklist_id)

    if is_leader(request.user):
        assignments_qs = checklist.assignments.select_related('executor', 'manager', 'audit').order_by('executor__full_name')
    else:
        assignments_qs = checklist.assignments.filter(manager=request.user).select_related('executor', 'manager', 'audit').order_by('executor__full_name')

    employee_query = request.GET.get('employee', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if employee_query:
        assignments_qs = assignments_qs.filter(executor__full_name__icontains=employee_query)

    if status_filter == 'not_created':
        assignments_qs = assignments_qs.filter(audit__isnull=True)
    elif status_filter == Audit.STATUS_DRAFT:
        assignments_qs = assignments_qs.filter(audit__status=Audit.STATUS_DRAFT)
    elif status_filter == Audit.STATUS_COMPLETED:
        assignments_qs = assignments_qs.filter(audit__status=Audit.STATUS_COMPLETED)

    if request.method == 'POST' and request.POST.get('action') == 'start_assigned_audit':
        assignment = get_object_or_404(assignments_qs, pk=request.POST.get('assignment_id'))

        audit, _ = Audit.objects.get_or_create(executor=assignment.executor, checklist=checklist)
        assignment.audit = audit
        if audit.status == Audit.STATUS_COMPLETED:
            assignment.status = ChecklistAssignment.STATUS_COMPLETED
        else:
            assignment.status = ChecklistAssignment.STATUS_IN_PROGRESS
        assignment.save(update_fields=['audit', 'status'])
        return redirect('audit_detail', audit_id=audit.id)

    return render(
        request,
        'audits/checklist_survey.html',
        {
            'checklist': checklist,
            'assignments': assignments_qs,
            'is_leader': is_leader(request.user),
            'employee_query': employee_query,
            'status_filter': status_filter,
        },
    )


@manager_required
def checklist_export_min(request, checklist_id):
    ensure_leader(request.user)
    checklist = get_object_or_404(Checklist, pk=checklist_id)
    data = build_checklist_assignments_export_workbook(checklist)
    response = HttpResponse(
        data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="checklist_{checklist.id}_min_export.xlsx"'
    return response



@manager_required
def checklist_export_answers(request, checklist_id):
    ensure_leader(request.user)
    checklist = get_object_or_404(Checklist, pk=checklist_id)
    data = build_checklist_answers_export_workbook(checklist)
    response = HttpResponse(
        data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="checklist_{checklist.id}_answers.xlsx"'
    return response

@manager_required
def audit_detail(request, audit_id):
    audit = get_object_or_404(Audit.objects.select_related('executor', 'checklist'), pk=audit_id)

    if request.method == 'POST' and request.POST.get('action') == 'change_status':
        status_form = AuditStatusForm(request.POST, instance=audit)
        if status_form.is_valid():
            status_form.save()
            ChecklistAssignment.objects.filter(audit=audit).update(
                status=ChecklistAssignment.STATUS_COMPLETED if audit.status == Audit.STATUS_COMPLETED else ChecklistAssignment.STATUS_IN_PROGRESS
            )
            messages.success(request, 'Статус аудита обновлен')
            return redirect('audit_detail', audit_id=audit.id)
    else:
        status_form = AuditStatusForm(instance=audit)

    sections = audit.checklist.sections.prefetch_related('items__fields__options').all().order_by('order', 'id')
    values = {
        v.field_id: v.value
        for v in AuditFieldValue.objects.filter(audit=audit).select_related('field')
    }

    return render(
        request,
        'audits/audit_detail.html',
        {
            'audit': audit,
            'sections': sections,
            'values': values,
            'status_form': status_form,
        },
    )


@manager_required
@require_POST
def audit_autosave(request, audit_id):
    audit = get_object_or_404(Audit, pk=audit_id)
    field_id = request.POST.get('field_id')
    value = request.POST.get('value', '')

    try:
        field = ChecklistField.objects.prefetch_related('options').get(pk=field_id, item__section__checklist=audit.checklist)
    except ChecklistField.DoesNotExist as exc:
        raise Http404 from exc

    if field.field_type == ChecklistField.TYPE_NUMBER and value:
        try:
            float(value.replace(',', '.'))
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'Для поля требуется число'}, status=400)

    if field.field_type == ChecklistField.TYPE_SELECT and value:
        allowed = set(field.options.values_list('value', flat=True))
        if value not in allowed:
            return JsonResponse({'ok': False, 'error': 'Выбрано недопустимое значение'}, status=400)

    answer, _ = AuditFieldValue.objects.get_or_create(audit=audit, field=field)
    answer.value = value
    answer.save(update_fields=['value'])

    return JsonResponse({'ok': True})


@manager_required
def reports_page(request):
    ensure_leader(request.user)

    total = Executor.objects.count()
    passed = Audit.objects.filter(status=Audit.STATUS_COMPLETED).values('executor_id').distinct().count()
    remaining = max(total - passed, 0)

    return render(
        request,
        'audits/reports.html',
        {
            'total': total,
            'passed': passed,
            'remaining': remaining,
        },
    )


@manager_required
def export_matrix(request):
    ensure_leader(request.user)
    data = build_export_matrix_workbook()
    response = HttpResponse(
        data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="audit_matrix.xlsx"'
    return response


@manager_required
def export_rows(request):
    ensure_leader(request.user)
    data = build_export_rows_workbook()
    response = HttpResponse(
        data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="audit_rows.xlsx"'
    return response












