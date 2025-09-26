from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.html import format_html

from .models import Profile, Role, UserRole

User = get_user_model()


# ------------------------
# Inlines for User admin
# ------------------------
class UserRoleInline(admin.TabularInline):
    """
    Inline to manage UserRole mappings from the User admin.
    Editable fields: role, is_active, assigned_by, note
    Readonly fields: assigned_at, revoked_at
    """
    model = UserRole
    fk_name = "user"
    extra = 0
    fields = ("role", "is_active", "assigned_by", "note", "assigned_at", "revoked_at")
    readonly_fields = ("assigned_at", "revoked_at")
    raw_id_fields = ("role", "assigned_by")
    ordering = ("-assigned_at",)
    verbose_name = "Role mapping"
    verbose_name_plural = "Role mappings"


class ProfileInline(admin.StackedInline):
    """
    Inline to display/edit Profile fields on the User admin page.
    """
    model = Profile
    can_delete = False
    verbose_name_plural = "profile"
    fk_name = "user"
    fields = ("phone", "profile_pic", "bio", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


# ------------------------
# Role admin
# ------------------------
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    actions = ("activate_roles", "deactivate_roles")

    def activate_roles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} role(s) activated.")
    activate_roles.short_description = "Activate selected roles"

    def deactivate_roles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} role(s) deactivated.")
    deactivate_roles.short_description = "Deactivate selected roles"


# ------------------------
# UserRole admin
# ------------------------
@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_active", "assigned_at", "revoked_at", "assigned_by", "note")
    list_filter = ("is_active", "role")
    search_fields = ("user__username", "user__email", "role__name", "role__slug")
    readonly_fields = ("assigned_at", "revoked_at")
    raw_id_fields = ("user", "role", "assigned_by")
    actions = ("revoke_mappings", "activate_mappings")

    def revoke_mappings(self, request, queryset):
        count = 0
        for ur in queryset:
            if ur.is_active:
                ur.revoke(by=request.user)
                count += 1
        self.message_user(request, f"{count} mapping(s) revoked.")
    revoke_mappings.short_description = "Revoke selected user-role mappings (set inactive)"

    def activate_mappings(self, request, queryset):
        count = 0
        for ur in queryset:
            if not ur.is_active:
                ur.activate(by=request.user)
                count += 1
        self.message_user(request, f"{count} mapping(s) activated.")
    activate_mappings.short_description = "Activate selected user-role mappings"


# ------------------------
# Extend the built-in User admin to include Profile and UserRole inlines
# ------------------------
# Unregister default User admin (if registered) and register a new one with inlines
try:
    admin.site.unregister(User)
except Exception:
    # If it wasn't registered yet, ignore
    pass


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    inlines = (ProfileInline, UserRoleInline)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "get_roles")

    def get_roles(self, obj):
        """Show comma-separated active roles for quick glance."""
        roles = Role.objects.filter(userrole__user=obj, userrole__is_active=True, is_active=True).distinct()
        return ", ".join([r.slug for r in roles])
    get_roles.short_description = "Active roles"
