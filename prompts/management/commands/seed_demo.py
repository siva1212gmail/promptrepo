import os
import io
import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from core.models import SiteSettings
from prompts.models import Category, Prompt, PromptLike
from requests_app.models import PromptRequest


def create_demo_image(title, subtitle="", theme="lime", width=800, height=1000, is_before=False, is_after=False):
    """
    Generates a dark-themed aesthetic poster card using Pillow.
    """
    # Base background palette
    color_palettes = {
        "lime": ((14, 14, 14), (204, 242, 13)),
        "cyan": ((10, 18, 24), (56, 189, 248)),
        "amber": ((20, 15, 10), (245, 158, 11)),
        "purple": ((18, 12, 26), (192, 132, 252)),
        "rose": ((24, 10, 16), (251, 113, 133)),
    }
    bg_color, accent_color = color_palettes.get(theme, ((14, 14, 14), (204, 242, 13)))
    
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw gradient glow or decorative circles
    if is_before:
        # Dull/flat look for "Before"
        draw.rectangle([(0, 0), (width, height)], fill=(32, 32, 35))
        accent_color = (156, 163, 175)
    elif is_after:
        # Vivid glowing render for "After"
        draw.ellipse([(width * 0.2, height * 0.1), (width * 0.8, height * 0.7)], fill=(accent_color[0]//4, accent_color[1]//4, accent_color[2]//4))
    else:
        # Standard card
        draw.ellipse([(width * 0.1, height * 0.2), (width * 0.9, height * 0.8)], fill=(accent_color[0]//5, accent_color[1]//5, accent_color[2]//5))

    # Grid / geometric lines
    for y in range(0, height, 80):
        draw.line([(0, y), (width, y)], fill=(255, 255, 255, 12), width=1)
    for x in range(0, width, 80):
        draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 12), width=1)

    # Frame border
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=accent_color, width=2)
    draw.rectangle([(26, 26), (width - 26, height - 26)], outline=(255, 255, 255, 30), width=1)

    # Top badges
    status_label = "BEFORE RAW" if is_before else ("AFTER 8K RENDER" if is_after else "PROMPT PETTI ORIGINAL")
    draw.text((40, 45), f"VOL.01 // {status_label}", fill=accent_color)
    draw.text((width - 160, 45), "@aswinthefilmer", fill=(200, 200, 200))

    # Center card illustration
    center_y = height // 2
    draw.rectangle([(width * 0.15, center_y - 120), (width * 0.85, center_y + 120)], fill=(0, 0, 0, 180), outline=accent_color, width=2)

    # Title & Subtitle text inside card
    # Fallback to default bitmap font safely
    draw.text((width * 0.2, center_y - 80), "✦ AI PROMPT DROP ✦", fill=accent_color)
    
    # Word wrap title
    words = title.split()
    line1 = " ".join(words[:4])
    line2 = " ".join(words[4:8])
    line3 = " ".join(words[8:])
    draw.text((width * 0.2, center_y - 40), line1, fill=(255, 255, 255))
    if line2:
        draw.text((width * 0.2, center_y - 10), line2, fill=(255, 255, 255))
    if line3:
        draw.text((width * 0.2, center_y + 20), line3, fill=(255, 255, 255))
    
    if subtitle:
        draw.text((width * 0.2, center_y + 60), f"// {subtitle}", fill=(180, 180, 180))

    # Bottom watermark & drop badge
    draw.text((40, height - 60), "CHATGPT & GEMINI AI PROMPTS", fill=(140, 140, 140))
    draw.text((width - 180, height - 60), "DAILY DROP 6 PM", fill=accent_color)

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=85)
    output.seek(0)
    return ContentFile(output.read())


class Command(BaseCommand):
    help = "Seeds database with categories, rich sample prompts, images, site settings, and test admin."

    def handle(self, *args, **options):
        self.stdout.write("Starting demo seed for Prompt Petti...")

        # 1. Site Settings
        settings = SiteSettings.load()
        settings.youtube_channel_url = "https://youtube.com/@aswinthefilmer?sub_confirmation=1"
        settings.instagram_url = "https://instagram.com/aswinthefilmer"
        settings.whatsapp_url = "https://whatsapp.com/channel/aswinthefilmer"
        settings.daily_drop_time = "18:00"
        settings.timezone = "Asia/Kolkata"
        settings.unlocked_today_base = 2243
        settings.save()
        self.stdout.write(self.style.SUCCESS("✓ Site settings configured."))

        # 2. Admin superuser
        admin_user, created = User.objects.get_or_create(username="admin")
        if created:
            admin_user.set_password("admin123")
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("✓ Created admin superuser (admin / admin123)."))
        else:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write("✓ Admin superuser already exists.")

        # 3. Categories (Portrait, Couple Prompts, Festive, Birthday, Cinematic, General, Stories, Surreal)
        categories_data = [
            ("Portrait", 1),
            ("Couple Prompts", 2),
            ("Festive", 3),
            ("Birthday", 4),
            ("Cinematic", 5),
            ("General", 6),
            ("Stories", 7),
            ("Surreal", 8),
        ]
        cat_map = {}
        for name, order in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'order': order})
            cat_map[name] = cat
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(cat_map)} categories with consistent capitalization."))

        # 4. Rich Sample Prompts
        sample_prompts = [
            {
                "title": "Kerala Kathakali Cyberpunk in Neon Kochi Monsoon",
                "category": "Cinematic",
                "type": "image",
                "theme": "lime",
                "has_ba": True,
                "like_count": 449,
                "is_featured": True,
                "prompt_text": (
                    "A hyper-realistic cinematic portrait of a traditional Kathakali dancer in full green Aharya makeup and majestic golden Kireedam headdress, illuminated by vibrant neon cyberpunk signage reflecting off wet asphalt in a rainy Fort Kochi alley. Atmospheric steam, photorealistic water droplet reflections on the intricate facial paint, anamorphic lens flare, 35mm film grain, 8k octane render, hyper-detailed textiles with golden zari embroidery, dramatic rim lighting, cinematic color grading inspired by Blade Runner 2049."
                ),
            },
            {
                "title": "Madurai Meenakshi Temple Tower Golden Hour Drone Fly-Through",
                "category": "Surreal",
                "type": "video",
                "theme": "amber",
                "has_ba": False,
                "like_count": 137,
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "is_featured": True,
                "prompt_text": (
                    "FPV cinematic drone camera descending slowly from golden sunset clouds into the vibrant South Gopuram tower of Madurai Meenakshi Amman Temple. Thousands of intricately carved Hindu deities painted in polychrome colors, bathed in warm 24k sunset sunlight. Flocks of temple pigeons taking flight in slow motion 60fps, holy camphor smoke gently drifting from below, majestic choir strings score in ambient atmosphere, shot on RED Digital Cinema 8K."
                ),
            },
            {
                "title": "Chennai Marina Beach Sunset Monsoon Couple Silhouette",
                "category": "Couple Prompts",
                "type": "image",
                "theme": "rose",
                "has_ba": True,
                "like_count": 132,
                "is_featured": True,
                "prompt_text": (
                    "A romantic cinematic wide shot of an Indian couple standing barefoot at Chennai Marina Beach as dramatic monsoon storm clouds roll in over the Bay of Bengal. Golden hour light breaking through purple-tinted rain clouds, sea breeze blowing the woman's emerald green silk saree pallu gracefully. Gentle ocean foam brushing against their feet on the wet golden sand with mirror reflections. Candid emotive expression, 85mm f/1.4 portrait lens, dreamy soft bokeh, Kodachrome vintage color palette."
                ),
            },
            {
                "title": "Retro 90s Tamil Cinema Ilaiyaraaja Cassette Room Vibe",
                "category": "Festive",
                "type": "image",
                "theme": "purple",
                "has_ba": False,
                "like_count": 108,
                "prompt_text": (
                    "Nostalgic 1990s South Indian bedroom aesthetic, featuring a vintage National Panasonic cassette deck player glowing in amber, stacked with original Ilaiyaraaja magnetic cassette tapes. Warm wooden table with an old stainless steel tumbler of steaming filter coffee, classic brass lamp, Madras checks curtain swaying in the morning breeze. Shot on 35mm analog film, warm nostalgic color tones, subtle dust particles in sunlight beam."
                ),
            },
            {
                "title": "Munnar Tea Estate Misty Morning Studio Portrait",
                "category": "Portrait",
                "type": "image",
                "theme": "cyan",
                "has_ba": True,
                "like_count": 95,
                "prompt_text": (
                    "Studio-quality outdoor portrait of a young South Indian woman wearing a handwoven terracotta cotton kurta, standing amidst rolling hills of misty emerald tea plantations in Munnar, Kerala. Early morning fog blankets the background, dew drops glistening on fresh tea leaves. Soft diffused morning sunlight, natural skin textures with subtle freckles, sharp catchlight in her expressive dark eyes, Hasselblad H6D-100c medium format."
                ),
            },
            {
                "title": "Grand Kerala Onam Sadhya Feast Micro-Macro Food Cinematic",
                "category": "Festive",
                "type": "video",
                "theme": "lime",
                "has_ba": False,
                "like_count": 89,
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "prompt_text": (
                    "Extreme macro slow-motion camera gliding across a fresh plantain leaf laden with 26 authentic Onam Sadhya dishes. Golden steaming hot Payasam being drizzled with roasted cashews and golden raisins, crispy upperi banana chips with textured jaggery coating, vibrant beetroot pachadi, creamy avial. Delicious steam rising, warm festive lighting, sound of temple melam in the backdrop, filmed at 120fps 4K macro."
                ),
            },
            {
                "title": "Traditional South Indian Royal 1st Birthday Baby Portrait",
                "category": "Birthday",
                "type": "image",
                "theme": "amber",
                "has_ba": False,
                "like_count": 84,
                "prompt_text": (
                    "Adorable 1-year-old Indian baby boy dressed like a little prince in traditional South Indian Kasavu dhoti with gold border and tiny royal crown, surrounded by fresh marigold garlands, brass Uruli filled with floating jasmine flowers and water diyas. Warm golden studio lighting, joyful radiant smile, hyper-detailed chubby cheeks and sparkling eyes, 50mm f/1.2 studio photography."
                ),
            },
            {
                "title": "Cyberpunk Neon Auto Rickshaw Ride Through Bangalore",
                "category": "Stories",
                "type": "video",
                "theme": "purple",
                "has_ba": False,
                "like_count": 77,
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "prompt_text": (
                    "First-person perspective riding in a futuristic high-tech Auto Rickshaw speeding through Bangalore's electronic city expressway at midnight. Glowing holographic meter display, neon cyan underglow, neon reflections on wet asphalt from towering AI tech skyscrapers. Electronic synthwave beats playing on the Rickshaw's custom LED speaker system, speed blur, cinematic night lighting."
                ),
            },
            {
                "title": "Cyberpunk Tanjore Painting with Glowing Gold Leaf",
                "category": "Surreal",
                "type": "image",
                "theme": "amber",
                "has_ba": True,
                "like_count": 72,
                "prompt_text": (
                    "A futuristic reinterpretation of traditional Thanjavur (Tanjore) painting style. Sacred divine artwork embedded with glowing fiber-optic gold leaf and authentic uncut gemstones that emit soft neon luminescence. Intricate gopuram arch frame carved with cybernetic motifs, high-relief plaster work with 22-carat gold gilding, dramatic contrast between centuries-old spiritual heritage and sci-fi aesthetic, 8K ultra detail."
                ),
            },
            {
                "title": "Vallam Kali Kerala Snake Boat Race Cinematic Action",
                "category": "Cinematic",
                "type": "video",
                "theme": "lime",
                "has_ba": False,
                "like_count": 68,
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "prompt_text": (
                    "High-octane action camera mounted on the bow of a 100-foot Chundan Vallam (snake boat) as 100 oarsmen row in synchronized rhythm across Punnamada Lake, Alappuzha. Powerful water splashes in slow motion catching the afternoon sun, rhythmic chants of Vanchipattu boat songs, drone aerial view revealing hundreds of colorful spectator boats lining the banks, intense sports documentary style."
                ),
            },
            {
                "title": "Chettinad Palace Heritage Couple Royalty Shoot",
                "category": "Couple Prompts",
                "type": "image",
                "theme": "rose",
                "has_ba": False,
                "like_count": 63,
                "prompt_text": (
                    "Royal wedding portrait of an elegant Tamil couple in the grand courtyard of an authentic 19th-century Chettinad heritage mansion. Intricately carved Burmese teak pillars, Athangudi handmade patterned floor tiles, antique Belgian chandeliers casting warm ambient light. The bride wears a crimson Kanchipuram silk saree with antique temple jewelry; the groom in raw silk veshti. Regal posture, Vogue India editorial style."
                ),
            },
            {
                "title": "Futuristic AI Studio Lighting Portrait for Content Creators",
                "category": "Portrait",
                "type": "image",
                "theme": "cyan",
                "has_ba": False,
                "like_count": 59,
                "prompt_text": (
                    "Modern studio portrait of a confident male content creator in a dark minimalist studio setup. Two-point neon lighting: soft lime glow from the left (#CCF20D) and deep violet rim light from the right. Sharp facial contours, clean modern haircut, matte black oversized techwear hoodie, holding a high-end cine camera. Clean black background with subtle haze, 85mm portrait depth of field."
                ),
            },
            {
                "title": "Rainy Window Coffee Shop Mood in Ooty Hill Station",
                "category": "General",
                "type": "image",
                "theme": "lime",
                "has_ba": False,
                "like_count": 52,
                "prompt_text": (
                    "Cozy aesthetic shot inside a vintage hillside café in Ooty during heavy monsoon rain. Through the condensation-covered glass window, misty eucalyptus trees and colonial rooftops are softly blurred. On the dark rustic wooden table sits an artisan ceramic mug of hot chocolate with marshmallows, an open notebook with fountain pen sketches, warm candle flame. Lo-fi aesthetic, tranquil atmosphere."
                ),
            },
            {
                "title": "Lord Shiva Himalayan Cosmic Meditation Hyper-Realism",
                "category": "Surreal",
                "type": "image",
                "theme": "cyan",
                "has_ba": True,
                "like_count": 145,
                "is_featured": True,
                "prompt_text": (
                    "Breathtaking surreal depiction of Lord Shiva in deep transcendental meditation on a snowy Himalayan peak under a swirling cosmic galaxy sky. Crescent moon glowing delicately in matted Jata hair, gentle river Ganges cascading down, sacred blue throat (Neelakantha) with subtle sapphire luminescence. Rudraksha beads with hyper-detailed texture, trishul planted in snow with damru, ethereal twilight glow, 8k Unreal Engine 5 render."
                ),
            },
        ]

        # IST timezone
        ist = ZoneInfo("Asia/Kolkata")
        now = timezone.now()

        created_count = 0
        for i, item in enumerate(sample_prompts):
            title = item["title"]
            category = cat_map[item["category"]]
            theme = item.get("theme", "lime")
            has_ba = item.get("has_ba", False)
            like_count = item.get("like_count", 50)
            is_featured = item.get("is_featured", False)
            prompt_text = item["prompt_text"]
            ptype = item.get("type", "image")
            video_url = item.get("video_url")

            # Check if prompt already exists
            prompt = Prompt.objects.filter(title=title).first()
            if not prompt:
                # Generate cover image
                cover_file = create_demo_image(title, subtitle=f"{item['category']} Drop", theme=theme)
                
                before_file = None
                after_file = None
                if has_ba:
                    before_file = create_demo_image(title, subtitle="Raw Flat Camera Capture", theme="lime", is_before=True)
                    after_file = create_demo_image(title, subtitle="8K Ultra Render After Prompt", theme=theme, is_after=True)

                # All demo prompts set published before now so they are immediately live
                # Stagger publish_at slightly so order is clean
                drop_time = now - datetime.timedelta(hours=i*3)

                prompt = Prompt(
                    title=title,
                    category=category,
                    type=ptype,
                    prompt_text=prompt_text,
                    like_count=like_count,
                    is_published=True,
                    publish_at=drop_time,
                    is_featured=is_featured,
                    video_url=video_url,
                )
                prompt.cover_image.save(f"cover_{i+1}.webp", cover_file, save=False)
                if before_file:
                    prompt.before_image.save(f"before_{i+1}.webp", before_file, save=False)
                if after_file:
                    prompt.after_image.save(f"after_{i+1}.webp", after_file, save=False)
                prompt.save()
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {created_count} rich sample prompts with WebP images and before/after comparisons."))

        # 5. Sample Prompt Requests
        if not PromptRequest.objects.exists():
            PromptRequest.objects.create(
                text="Ghibli-style couple photo in Munnar tea garden rain",
                name_or_handle="@karthik_cine",
                status="new",
                ip_address="127.0.0.1"
            )
            PromptRequest.objects.create(
                text="Rajinikanth retro 80s Billa neon gangster aesthetic portrait",
                name_or_handle="Suresh K",
                status="seen",
                ip_address="127.0.0.1"
            )
            PromptRequest.objects.create(
                text="Traditional Kerala Onam boat race dynamic FPV video prompt for Gemini",
                name_or_handle="@anupama_v",
                status="done",
                ip_address="127.0.0.1"
            )
            self.stdout.write(self.style.SUCCESS("✓ Seeded sample prompt requests."))

        self.stdout.write(self.style.SUCCESS("All demo seeding completed successfully! Prompt Petti is ready."))
