# control_panel/admin.py
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import SystemSettings, AuditLog, BackupConfig, UsefulLink


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ["key", "value", "description", "updated_at"]
    list_editable = ["value"]
    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request):
        # Permite apenas uma instância
        return not SystemSettings.objects.exists()


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user", "action", "resource", "status", "ip_address"]
    list_filter = ["action", "status", "timestamp", "user"]
    search_fields = ["user__username", "resource", "ip_address"]
    readonly_fields = [
        "timestamp",
        "user",
        "action",
        "resource",
        "details",
        "status",
        "ip_address",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BackupConfig)
class BackupConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "enabled", "schedule", "last_run", "next_run"]
    list_editable = ["enabled", "schedule"]
    list_filter = ["enabled", "schedule"]
    actions = ["run_backup_now"]

    def run_backup_now(self, request, queryset):
        for backup_config in queryset:
            # Lógica de backup aqui
            self.message_user(
                request, f"Backup {backup_config.name} executado com sucesso!"
            )

    run_backup_now.short_description = "Executar backup agora"


@admin.register(UsefulLink)
class UsefulLinkAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "icon", "order", "is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["name", "url"]


# Customizar User Admin
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        "last_login",
        "is_active",
        "is_staff_display",
    )
    list_filter = UserAdmin.list_filter + ("is_staff", "is_superuser", "is_active")

    def is_staff_display(self, obj):
        return obj.is_staff

    is_staff_display.short_description = "Staff"
    is_staff_display.boolean = True


# Customizar Group Admin
class CustomGroupAdmin(GroupAdmin):
    list_display = ["name", "user_count"]

    def user_count(self, obj):
        return obj.user_set.count()

    user_count.short_description = "Usuários"


# Re-registrar User e Group com admin customizado
if admin.site.is_registered(User):
    admin.site.unregister(User)
if admin.site.is_registered(Group):
    admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)

# Customizar header do admin
admin.site.site_header = "SisCoE - Administração"
admin.site.site_title = "SisCoE Admin"
admin.site.index_title = "Painel de Administração"
