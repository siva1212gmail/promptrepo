import datetime
from zoneinfo import ZoneInfo
from django.utils import timezone
from .models import SiteSettings


def get_next_drop_datetime():
    """Returns the next 6:00 PM IST datetime as an aware datetime object."""
    ist = ZoneInfo("Asia/Kolkata")
    now_ist = timezone.now().astimezone(ist)
    drop_time = datetime.time(18, 0, 0)
    
    target_today = datetime.datetime.combine(now_ist.date(), drop_time, tzinfo=ist)
    if now_ist < target_today:
        return target_today
    else:
        tomorrow = now_ist.date() + datetime.timedelta(days=1)
        return datetime.datetime.combine(tomorrow, drop_time, tzinfo=ist)


def site_context(request):
    try:
        settings = SiteSettings.load()
    except Exception:
        settings = None

    next_drop = get_next_drop_datetime()
    is_unlocked = request.COOKIES.get('unlocked') == 'true' or request.session.get('unlocked') is True

    return {
        'site_settings': settings,
        'youtube_channel_url': settings.youtube_channel_url if settings else "https://youtube.com/@aswinthefilmer?sub_confirmation=1",
        'instagram_url': settings.instagram_url if settings else "https://instagram.com/aswinthefilmer",
        'whatsapp_url': settings.whatsapp_url if settings else "https://whatsapp.com/channel/aswinthefilmer",
        'unlocked_today_count': settings.today_unlocked_count if settings else 2289,
        'next_drop_iso': next_drop.isoformat(),
        'is_unlocked': is_unlocked,
    }
