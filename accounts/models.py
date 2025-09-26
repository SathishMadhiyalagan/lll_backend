# accounts/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify


def validate_image_size(image):
    """Simple validator: max 3 MB"""
    max_mb = 3
    if image and hasattr(image, "size") and image.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Image file too large ( > {max_mb}MB )")


def user_profile_pic_path(instance, filename):
    # e.g. profile_pics/user_5/avatar.jpg
    return f"profile_pics/user_{instance.user.id}/{filename}"


class Role(models.Model):
    """
    Role table. Keep roles soft-disabled via `is_active` so historical mappings remain.
    """
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # whether this role can be assigned/used
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    Profile (OneToOne) to hold extra user fields (profile_pic, phone, bio).
    Use profile.roles_* helpers to manage role mapping.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(
        max_length=20,
        blank=True, null=True,
        validators=[RegexValidator(regex=r'^\+?[0-9]{7,15}$',
                                   message="Phone must be digits, optionally starting with +, length 7-15.")]
    )
    profile_pic = models.ImageField(upload_to=user_profile_pic_path, blank=True, null=True, validators=[validate_image_size])
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_role(self, role_slug):
        """Return True if user has an active mapping to an active Role with slug=role_slug."""
        return UserRole.objects.filter(
            user=self.user,
            role__slug=role_slug,
            is_active=True,
            role__is_active=True
        ).exists()

    def get_active_roles(self):
        """Return queryset of active Role objects assigned to this user."""
        return Role.objects.filter(userrole__user=self.user, userrole__is_active=True, is_active=True)

    def add_role(self, role, assigned_by=None, note=None):
        """
        Assign a role to the user.
        - role: Role instance (must be saved).
        - assigned_by: optional User who assigned the role.
        If a mapping exists and is inactive, it will be re-activated and timestamp updated.
        """
        if not role.pk:
            raise ValueError("role must be saved (have a primary key) before assigning")
        if not role.is_active:
            raise ValueError("cannot assign an inactive Role")

        ur, created = UserRole.objects.get_or_create(user=self.user, role=role, defaults={
            "assigned_by": assigned_by,
            "note": note,
            "is_active": True,
            "assigned_at": timezone.now()
        })
        if not created:
            # if existing mapping, ensure it's active and update metadata
            ur.is_active = True
            ur.assigned_by = assigned_by or ur.assigned_by
            if note:
                ur.note = note
            ur.assigned_at = timezone.now()
            ur.save()
        return ur

    def remove_role(self, role):
        """
        Soft-remove a role mapping (set is_active=False).
        """
        UserRole.objects.filter(user=self.user, role=role, is_active=True).update(is_active=False, revoked_at=timezone.now())

    def __str__(self):
        return f"Profile for {self.user.get_username()}"


class UserRole(models.Model):
    """
    Through table mapping user <-> role so we can store metadata per assignment.
    - is_active: if False, the mapping is treated as disabled (user no longer has that role).
    - assigned_at / revoked_at: timestamps.
    - assigned_by: optional user who assigned the role.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="userrole")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="userrole")
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(blank=True, null=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_roles")
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("user", "role")
        ordering = ("-assigned_at",)
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

    def revoke(self, by=None):
        """Helper to revoke this mapping."""
        self.is_active = False
        self.revoked_at = timezone.now()
        if by:
            self.assigned_by = by
        self.save()

    def activate(self, by=None):
        """Activate/reactivate mapping."""
        self.is_active = True
        self.assigned_at = timezone.now()
        self.revoked_at = None
        if by:
            self.assigned_by = by
        self.save()

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.user.get_username()} -> {self.role.slug} ({status})"


# Ensure a Profile is created for each new User
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # ensure profile exists (useful when adding this model to an existing project)
        Profile.objects.get_or_create(user=instance)
