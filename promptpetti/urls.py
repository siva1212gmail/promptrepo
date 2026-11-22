from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Custom Influencer Dashboard
    path('dashboard/', include('core.dashboard_urls', namespace='dashboard')),
    
    # Main public pages
    path('', core_views.home_view, name='home'),
    path('p/<slug:slug>/', core_views.prompt_detail_page, name='prompt_detail_page'),
    
    # Unlock and Request APIs
    path('api/unlock/', core_views.api_unlock, name='api_unlock'),
    path('api/requests/', core_views.api_submit_request, name='api_submit_request'),
    
    # Prompts APIs
    path('', include('prompts.urls', namespace='prompts')),
    
    # SEO
    path('robots.txt', core_views.robots_txt, name='robots_txt'),
    path('sitemap.xml', core_views.sitemap_xml, name='sitemap_xml'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
