import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from django.db import models
from django.utils import timezone


class SiteSettings(models.Model):
    youtube_channel_url = models.CharField(
        max_length=255,
        default="https://youtube.com/@aswinthefilmer?sub_confirmation=1",
        help_text="Direct link to YouTube channel or subscribe link"
    )
    instagram_url = models.CharField(
        max_length=255,
        default="https://instagram.com/aswinthefilmer",
        blank=True
    )
    whatsapp_url = models.CharField(
        max_length=255,
        default="https://whatsapp.com/channel/aswinthefilmer",
        blank=True
    )
    daily_drop_time = models.TimeField(
        default="18:00",
        help_text="Time of daily drop in IST (e.g. 18:00)"
    )
    timezone = models.CharField(
        max_length=64,
        default="Asia/Kolkata"
    )
    unlocked_today_base = models.PositiveIntegerField(
        default=2243,
        help_text="Base number for 'people unlocked today'"
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Prompt Petti Site Settings"

    def save(self, *args, **kwargs):
        # Force single row
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def today_unlocked_count(self):
        """
        Admin-editable base number plus a small random-but-stable daily offset
        based on today's date in IST.
        """
        tz = ZoneInfo(self.timezone or "Asia/Kolkata")
        today_str = timezone.now().astimezone(tz).strftime("%Y-%m-%d")
        # Deterministic pseudo-random offset between 17 and 137 based on date hash
        hash_val = int(hashlib.md5(f"unlock-{today_str}".encode()).hexdigest()[:6], 16)
        daily_offset = (hash_val % 120) + 17
        return self.unlocked_today_base + daily_offset
