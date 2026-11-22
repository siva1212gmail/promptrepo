from django.db import models


class PromptRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('seen', 'Seen'),
        ('done', 'Done'),
    ]

    text = models.CharField(
        max_length=180,
        help_text="What should I drop next? (max 180 chars)"
    )
    name_or_handle = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional name or @handle"
    )
    reference_image = models.ImageField(
        upload_to='requests/%Y/%m/',
        blank=True,
        null=True,
        help_text="Optional reference image attachment"
    )
    reference_link = models.URLField(
        blank=True,
        null=True,
        help_text="Optional link to reference image, video, or inspiration"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prompt Request"
        verbose_name_plural = "Prompt Requests"
        ordering = ['-created_at']

    def __str__(self):
        name = self.name_or_handle or "Anonymous"
        return f"{name}: {self.text[:40]}"
