from django.db import models
from uuid import UUID as PyUUID


class GithubRun(models.Model):
    """
    Represents a build job triggered via GitHub Actions for custom RustDesk clients.
    """

    PLATFORM_CHOICES = [
        ('windows', 'Windows (64-bit)'),
        ('windows-x86', 'Windows (32-bit)'),
        ('linux', 'Linux'),
        ('macos', 'macOS'),
        ('android', 'Android'),
    ]

    STATUS_CHOICES = [
        ('InProgress', 'In Progress'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]

    uuid = models.CharField(
        max_length=36,
        unique=True,
        help_text="UUID used to identify the build and associated assets (PNGs, EXE, etc.)"
    )
    filename = models.CharField(
        max_length=255,
        help_text="Custom executable name (e.g., 'mydesk.exe')"
    )
    direction = models.CharField(
        max_length=20,
        help_text="Connection type: 'direct' or 'relay'"
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        help_text="Target OS/platform for the build"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='InProgress',
        help_text="Current status of the GitHub Action workflow"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "GitHub Build Run"
        verbose_name_plural = "GitHub Build Runs"
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['status']),
            models.Index(fields=['platform']),
        ]

    def __str__(self):
        return f"{self.filename} ({self.platform}) - {self.status}"

    def clean(self):
        # Validate UUID format
        try:
            PyUUID(self.uuid)
        except ValueError:
            raise models.ValidationError({'uuid': 'Invalid UUID format.'})
        super().clean()
