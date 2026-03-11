from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('executors', views.executors_list, name='executors_list'),
    path('executors/import', views.executors_import, name='executors_import'),
    path('executors/<int:executor_id>', views.executor_detail, name='executor_detail'),
    path('audit/<int:audit_id>', views.audit_detail, name='audit_detail'),
    path('audit/<int:audit_id>/autosave', views.audit_autosave, name='audit_autosave'),
    path('checklists', views.checklists_page, name='checklists_page'),
    path('checklists/<int:checklist_id>', views.checklist_detail, name='checklist_detail'),
    path('checklists/<int:checklist_id>/survey', views.checklist_survey, name='checklist_survey'),
    path('checklists/<int:checklist_id>/export-min', views.checklist_export_min, name='checklist_export_min'),
    path('checklists/<int:checklist_id>/export-answers', views.checklist_export_answers, name='checklist_export_answers'),
    path('survey', views.survey_list, name='survey_list'),
    path('reports', views.reports_page, name='reports_page'),
    path('reports/export/matrix', views.export_matrix, name='export_matrix'),
    path('reports/export/rows', views.export_rows, name='export_rows'),
]

