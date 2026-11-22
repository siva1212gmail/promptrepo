import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import PromptRequest


@admin.action(description="Mark selected requests as Done")
def mark_as_done(modeladmin, request, queryset):
    updated = queryset.update(status='done')
    modeladmin.message_user(request, f"{updated} request(s) marked as done.")


@admin.action(description="Mark selected requests as Seen")
def mark_as_seen(modeladmin, request, queryset):
    updated = queryset.update(status='seen')
    modeladmin.message_user(request, f"{updated} request(s) marked as seen.")


@admin.action(description="Export selected requests to CSV")
def export_requests_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="prompt_requests.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Status', 'Name/Handle', 'Request Text', 'Reference Link', 'Has Image', 'IP Address', 'Created At'])
    for obj in queryset:
        writer.writerow([
            obj.id,
            obj.status,
            obj.name_or_handle,
            obj.text,
            obj.reference_link or '',
            'Yes' if obj.reference_image else 'No',
            obj.ip_address or '',
            obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    return response


@admin.register(PromptRequest)
class PromptRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'status_badge',
        'text_snippet',
        'name_or_handle_display',
        'image_preview',
        'link_preview',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('text', 'name_or_handle', 'ip_address')
    actions = [mark_as_done, mark_as_seen, export_requests_csv]
    readonly_fields = ('image_preview_large', 'created_at')

    def text_snippet(self, obj):
        return obj.text[:60] + ('...' if len(obj.text) > 60 else '')
    text_snippet.short_description = "Request"

    def name_or_handle_display(self, obj):
        return obj.name_or_handle or "Anonymous"
    name_or_handle_display.short_description = "Requester"

    def status_badge(self, obj):
        colors = {
            'new': '#CCF20D',
            'seen': '#38bdf8',
            'done': '#9ca3af'
        }
        text_colors = {
            'new': '#000000',
            'seen': '#000000',
            'done': '#ffffff'
        }
        bg = colors.get(obj.status, '#6b7280')
        fg = text_colors.get(obj.status, '#ffffff')
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 8px; border-radius:12px; font-weight:700; font-size:11px; text-transform:uppercase;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def image_preview(self, obj):
        if obj.reference_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="width:40px; height:40px; object-fit:cover; border-radius:4px; border:1px solid #444;" /></a>',
                obj.reference_image.url, obj.reference_image.url
            )
        return "-"
    image_preview.short_description = "Attachment"

    def image_preview_large(self, obj):
        if obj.reference_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width:320px; border-radius:8px;" /></a>',
                obj.reference_image.url, obj.reference_image.url
            )
        return "No image attached"
    image_preview_large.short_description = "Full Attachment"

    def link_preview(self, obj):
        if obj.reference_link:
            return format_html(
                '<a href="{}" target="_blank" style="color:#CCF20D; text-decoration:underline;">View Link ↗</a>',
                obj.reference_link
            )
        return "-"
    link_preview.short_description = "Link"
