import os
import io
import datetime
from zoneinfo import ZoneInfo
from PIL import Image
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile


def get_default_publish_time():
    """
    Default publish_at to the next 6:00 PM IST
    (today if currently before 6 PM, otherwise tomorrow at 6 PM).
    """
    ist = ZoneInfo("Asia/Kolkata")
    now_ist = timezone.now().astimezone(ist)
    drop_time = datetime.time(18, 0, 0)
    
    today_drop = datetime.datetime.combine(now_ist.date(), drop_time, tzinfo=ist)
    if now_ist < today_drop:
        return today_drop
    else:
        tomorrow = now_ist.date() + datetime.timedelta(days=1)
        return datetime.datetime.combine(tomorrow, drop_time, tzinfo=ist)


def optimize_uploaded_image(image_field, max_dimension=1600, quality=85):
    """
    Optimizes uploaded image to WebP format for high performance and low bandwidth.
    """
    if not image_field or not hasattr(image_field, 'file'):
        return
    try:
        image = Image.open(image_field)
        image_format = (image.format or 'JPEG').upper()
        if image.mode in ('RGBA', 'LA') and image_format != 'WEBP':
            # Keep transparency
            pass
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if exceeding max_dimension
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        output_io = io.BytesIO()
        image.save(output_io, format='WEBP', quality=quality, optimize=True)
        output_io.seek(0)
        
        base_name = os.path.splitext(os.path.basename(image_field.name))[0]
        new_name = f"{base_name}.webp"
        image_field.save(new_name, ContentFile(output_io.read()), save=False)
    except Exception:
        # If optimization fails (e.g., SVG or video file), leave untouched
        pass


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Sorting order in pills list")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PublishedPromptManager(models.Manager):
    """Query manager returning only publicly live prompts (published & drop time passed)."""
    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(is_published=True, publish_at__lte=now)


class Prompt(models.Model):
    TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='image')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='prompts'
    )
    prompt_text = models.TextField(
        help_text="Protected prompt text. Visitors must unlock to view."
    )
    cover_image = models.ImageField(
        upload_to='prompts/covers/',
        help_text="Main preview image / video thumbnail"
    )
    before_image = models.ImageField(
        upload_to='prompts/before/',
        blank=True,
        null=True,
        help_text="Optional: Image BEFORE AI transformation"
    )
    after_image = models.ImageField(
        upload_to='prompts/after/',
        blank=True,
        null=True,
        help_text="Optional: Image AFTER AI transformation"
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        help_text="Optional YouTube / Instagram / Shorts video URL"
    )
    video_file = models.FileField(
        upload_to='prompts/videos/',
        blank=True,
        null=True,
        help_text="Optional MP4 video file"
    )
    like_count = models.PositiveIntegerField(
        default=0,
        help_text="Base like count editable by admin (e.g. 449, 137)"
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Whether prompt is approved to be published"
    )
    publish_at = models.DateTimeField(
        default=get_default_publish_time,
        help_text="Scheduled publish time (defaults to next 6:00 PM IST)"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured in hero or pinned spots"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()  # The default manager (all items)
    published = PublishedPromptManager()  # Only live items

    class Meta:
        verbose_name = "Prompt"
        verbose_name_plural = "Prompts"
        ordering = ['-publish_at', '-id']

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"

    @property
    def is_live(self):
        return self.is_published and self.publish_at <= timezone.now()

    @property
    def is_new(self):
        """New badge if published within the last 24 hours."""
        if not self.is_live:
            return False
        cutoff = timezone.now() - datetime.timedelta(hours=24)
        return self.publish_at >= cutoff

    @property
    def has_before_after(self):
        return bool(self.before_image and self.after_image)

    @property
    def total_likes(self):
        return self.like_count + self.likes.count()

    def get_absolute_url(self):
        return f"/p/{self.slug}/"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "prompt"
            unique_slug = base_slug
            counter = 1
            while Prompt.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        
        # Optimize cover image if new
        if self.cover_image and hasattr(self.cover_image, 'file'):
            try:
                if not self.cover_image.name.endswith('.webp'):
                    optimize_uploaded_image(self.cover_image)
            except Exception:
                pass

        super().save(*args, **kwargs)


class PromptLike(models.Model):
    """
    Lightweight like tracking per browser/visitor.
    """
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='likes')
    visitor_id = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('prompt', 'visitor_id')
        verbose_name = "Prompt Like"
        verbose_name_plural = "Prompt Likes"

    def __str__(self):
        return f"Like for {self.prompt_id} by {self.visitor_id}"
