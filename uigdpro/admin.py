# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import GithubRun


@admin.register(GithubRun)
class GithubRunAdmin(admin.ModelAdmin):
    list_display = (
        'filename',
        'platform_badge',
        'direction',
        'status_badge',
        'uuid_short',
        'created_at',
        'download_link',
    )
    list_filter = ('platform', 'status', 'direction', 'created_at')
    search_fields = ('uuid', 'filename')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Build Info', {
            'fields': ('uuid', 'filename', 'platform', 'direction')
        }),
        ('Status & Timing', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

    # Custom display methods
    def platform_badge(self, obj):
        colors = {
            'windows': '#0078d4',
            'windows-x86': '#0078d4',
            'linux': '#339900',
            'macos': '#e53935',
            'android': '#3ddc84',
        }
        color = colors.get(obj.platform, '#666')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 4px;">{}</span>',
            color,
            obj.get_platform_display()
        )
    platform_badge.short_description = "Platform"

    def status_badge(self, obj):
        colors = {
            'InProgress': '#ff9800',
            'Success': '#4caf50',
            'Failed': '#f44336',
            'Cancelled': '#9e9e9e',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<strong><span style="color: {};">●</span> {}</strong>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def uuid_short(self, obj):
        return obj.uuid[:8]
    uuid_short.short_description = "UUID (short)"


    def download_link(self, obj):
        if obj.status == 'Success':
            from django.urls import reverse
            url = reverse('download') + f'?uuid={obj.uuid}&filename={obj.filename}'
            return format_html('<a href="{}" target="_blank">⬇️ Download</a>', url)
        return "—"


    # def has_add_permission(self, request):
    #     return False


    actions = ['mark_as_failed']

    @admin.action(description="Mark selected runs as Failed")
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='Failed')
        self.message_user(request, f"{updated} build(s) marked as Failed.")
