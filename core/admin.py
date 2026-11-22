from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'daily_drop_time', 'timezone', 'unlocked_today_base', 'today_unlocked_preview')
    fieldsets = (
        ("Channel & Social Links", {
            'fields': ('youtube_channel_url', 'instagram_url', 'whatsapp_url')
        }),
        ("Daily Drop Schedule", {
            'fields': ('daily_drop_time', 'timezone')
        }),
        ("Unlock Counter", {
            'description': "Base number for 'people unlocked today' shown on the locked prompt box.",
            'fields': ('unlocked_today_base',)
        }),
    )

    def today_unlocked_preview(self, obj):
        return f"{obj.today_unlocked_count} (calculated for today)"
    today_unlocked_preview.short_description = "Today's Displayed Unlocks"

    def has_add_permission(self, request):
        # Disallow adding more than one settings object
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
