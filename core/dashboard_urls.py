from django.urls import path
from . import dashboard_views as dv

app_name = 'dashboard'

urlpatterns = [
    path('', dv.dashboard_overview, name='overview'),
    path('prompts/', dv.dashboard_prompts_list, name='prompts_list'),
    path('prompts/add/', dv.dashboard_prompt_add, name='prompt_add'),
    path('prompts/<int:prompt_id>/edit/', dv.dashboard_prompt_edit, name='prompt_edit'),
    path('prompts/<int:prompt_id>/delete/', dv.dashboard_prompt_delete, name='prompt_delete'),
    path('prompts/<int:prompt_id>/publish-now/', dv.dashboard_prompt_publish_now, name='prompt_publish_now'),
    path('requests/', dv.dashboard_requests_list, name='requests_list'),
    path('requests/<int:request_id>/done/', dv.dashboard_request_mark_done, name='request_mark_done'),
    path('requests/export-csv/', dv.dashboard_export_requests_csv, name='requests_export_csv'),
    path('settings/', dv.dashboard_settings_view, name='settings'),
    path('categories/', dv.dashboard_categories_view, name='categories'),
]
