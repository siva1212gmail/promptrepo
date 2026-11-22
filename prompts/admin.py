import csv
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponse

from .models import Category, Prompt, PromptLike


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'prompt_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('order', 'name')

    def prompt_count(self, obj):
        return obj.prompts.count()
    prompt_count.short_description = "Prompts"


@admin.action(description="Publish selected prompts immediately")
def make_published_now(modeladmin, request, queryset):
    now = timezone.now()
    updated = queryset.update(is_published=True, publish_at=now)
    modeladmin.message_user(request, f"{updated} prompt(s) published immediately.")


@admin.action(description="Unpublish selected prompts")
def make_unpublished(modeladmin, request, queryset):
    updated = queryset.update(is_published=False)
    modeladmin.message_user(request, f"{updated} prompt(s) unpublished.")


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail_preview',
        'title',
        'category',
        'type_badge',
        'schedule_status',
        'like_count_display',
        'is_featured',
    )
    list_filter = ('type', 'category', 'is_published', 'is_featured')
    search_fields = ('title', 'prompt_text', 'category__name')
    prepopulated_fields = {'slug': ('title',)}
    actions = [make_published_now, make_unpublished]
    readonly_fields = ('thumbnail_preview_large', 'created_at', 'updated_at')
    fieldsets = (
        ("Basic Information", {
            'fields': ('title', 'slug', 'category', 'type', 'is_featured')
        }),
        ("Prompt Secret Text", {
            'description': "Protected prompt text. Visitors must unlock to view.",
            'fields': ('prompt_text',)
        }),
        ("Media & Comparison", {
            'fields': (
                'cover_image',
                'thumbnail_preview_large',
                'before_image',
                'after_image',
                'video_url',
                'video_file',
            )
        }),
        ("Drop Schedule & Status", {
            'fields': ('is_published', 'publish_at', 'like_count')
        }),
        ("Timestamps", {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    def thumbnail_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px; border: 1px solid #CCF20D;" />',
                obj.cover_image.url
            )
        return "-"
    thumbnail_preview.short_description = "Cover"

    def thumbnail_preview_large(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 240px; height: auto; border-radius: 8px; border: 2px solid #CCF20D;" />',
                obj.cover_image.url
            )
        return "No image uploaded"
    thumbnail_preview_large.short_description = "Image Preview"

    def type_badge(self, obj):
        bg = "#CCF20D" if obj.type == 'image' else "#38bdf8"
        color = "#000000"
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 8px; border-radius:12px; font-weight:700; font-size:11px; text-transform:uppercase;">{}</span>',
            bg, color, obj.get_type_display()
        )
    type_badge.short_description = "Type"

    def schedule_status(self, obj):
        now = timezone.now()
        if not obj.is_published:
            return format_html('<span style="color:#ef4444; font-weight:600;">Draft (Unpublished)</span>')
        if obj.publish_at > now:
            return format_html(
                '<span style="color:#f59e0b; font-weight:600;">⏳ Scheduled: {}</span>',
                obj.publish_at.strftime("%d %b %I:%M %p")
            )
        return format_html('<span style="color:#22c55e; font-weight:600;">● Live</span>')
    schedule_status.short_description = "Status / Schedule"

    def like_count_display(self, obj):
        return f"♥ {obj.total_likes}"
    like_count_display.short_description = "Likes"


@admin.register(PromptLike)
class PromptLikeAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'visitor_id', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('prompt__title', 'visitor_id', 'ip_address')
