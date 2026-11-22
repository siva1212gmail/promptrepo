from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    path('api/prompts/', views.api_prompt_list, name='api_list'),
    path('api/prompts/<int:prompt_id>/', views.api_prompt_detail, name='api_detail'),
    path('api/prompts/<int:prompt_id>/text/', views.api_prompt_text, name='api_text'),
    path('api/prompts/<int:prompt_id>/like/', views.api_prompt_like, name='api_like'),
]
