import uuid
import datetime
from zoneinfo import ZoneInfo
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, F

from .models import SiteSettings
from prompts.models import Prompt, Category, PromptLike
from requests_app.models import PromptRequest


def get_client_ip(request):
    """Safely extracts client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'


def is_visitor_unlocked(request):
    """Check if visitor has unlocked prompts via cookie or session."""
    return request.COOKIES.get('unlocked') == 'true' or request.session.get('unlocked') is True


@ensure_csrf_cookie
def home_view(request):
    """
    Renders the Prompt Petti home page with initial server-rendered prompt grid.
    """
    now = timezone.now()
    categories = Category.objects.all().prefetch_related('prompts')
    
    # Live prompts: published and drop time passed
    live_prompts = Prompt.published.all().select_related('category')
    
    # Most liked this week (top 8)
    most_liked = live_prompts.order_by('-like_count', '-created_at')[:8]
    
    # Server-rendered initial grid (first page of 12)
    initial_prompts = live_prompts[:12]
    
    # Calculate category counts for live prompts
    category_counts = {}
    for cat in categories:
        category_counts[cat.id] = cat.prompts.filter(is_published=True, publish_at__lte=now).count()
    
    context = {
        'categories': categories,
        'category_counts': category_counts,
        'most_liked': most_liked,
        'initial_prompts': initial_prompts,
        'total_live_count': live_prompts.count(),
        'initial_prompt_slug': None,
        'modal_prompt': None,
        'og_title': "Prompt Petti — Trending AI Image & Video Prompts by @aswinthefilmer",
        'og_description': "Trending image & video prompts for ChatGPT and Gemini — explained simply, with fresh drops every day.",
        'og_image': None,
        'og_url': request.build_absolute_uri(),
    }
    return render(request, 'index.html', context)


@ensure_csrf_cookie
def prompt_detail_page(request, slug):
    """
    Direct URL for a prompt (/p/<slug>/) with proper server-side Open Graph tags
    for WhatsApp/Instagram/Twitter previews, opening the modal on load.
    SECURITY: Prompt text is NOT included unless unlocked.
    """
    now = timezone.now()
    # Prompt can be viewed if published and live, or previewed by staff
    if request.user.is_staff:
        prompt = get_object_or_404(Prompt.objects.select_related('category'), slug=slug)
    else:
        prompt = get_object_or_404(Prompt.published.select_related('category'), slug=slug)
    
    categories = Category.objects.all().prefetch_related('prompts')
    live_prompts = Prompt.published.all().select_related('category')
    most_liked = live_prompts.order_by('-like_count', '-created_at')[:8]
    initial_prompts = live_prompts[:12]
    
    category_counts = {}
    for cat in categories:
        category_counts[cat.id] = cat.prompts.filter(is_published=True, publish_at__lte=now).count()

    cover_url = request.build_absolute_uri(prompt.cover_image.url) if prompt.cover_image else None

    context = {
        'categories': categories,
        'category_counts': category_counts,
        'most_liked': most_liked,
        'initial_prompts': initial_prompts,
        'total_live_count': live_prompts.count(),
        'initial_prompt_slug': prompt.slug,
        'modal_prompt': prompt,
        'og_title': f"{prompt.title} — Prompt Petti",
        'og_description': f"Trending AI {prompt.get_type_display()} Prompt for ChatGPT & Gemini by @aswinthefilmer.",
        'og_image': cover_url,
        'og_url': request.build_absolute_uri(prompt.get_absolute_url()),
    }
    return render(request, 'index.html', context)


@require_POST
def api_unlock(request):
    """
    Sets long-lived cookie unlocked=true (1 year) and session flag.
    No login or YouTube API verification needed.
    """
    request.session['unlocked'] = True
    response = JsonResponse({
        'success': True,
        'message': 'All prompts unlocked! Enjoy generating.'
    })
    # 1 year in seconds = 365 * 24 * 60 * 60 = 31,536,000
    one_year = 365 * 24 * 60 * 60
    response.set_cookie(
        'unlocked',
        'true',
        max_age=one_year,
        httponly=False,  # Accessible to client JS for UI state
        samesite='Lax',
        secure=not request.is_secure() if False else request.is_secure()
    )
    return response


@require_POST
def api_submit_request(request):
    """
    Submits a prompt request from visitor with rate limiting, honeypot,
    and file upload validation.
    """
    # Honeypot spam check
    honeypot = request.POST.get('website_url_hp', '').strip()
    if honeypot:
        # Silently return success to mislead spambots
        return JsonResponse({'success': True, 'message': 'Request received!'})

    ip = get_client_ip(request)
    
    # Rate limit check: max 5 requests per IP per hour
    one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
    recent_requests_count = PromptRequest.objects.filter(
        ip_address=ip,
        created_at__gte=one_hour_ago
    ).count()
    if recent_requests_count >= 5:
        return JsonResponse({
            'success': False,
            'error': 'Rate limit reached. Please wait an hour before submitting another prompt request.'
        }, status=429)

    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'success': False, 'error': 'Please enter what you want me to drop next.'}, status=400)
    if len(text) > 180:
        return JsonResponse({'success': False, 'error': 'Prompt request must be 180 characters or less.'}, status=400)

    name_or_handle = request.POST.get('name_or_handle', '').strip()[:100]
    reference_link = request.POST.get('reference_link', '').strip()
    reference_image = request.FILES.get('reference_image')

    # Validate image attachment if provided
    if reference_image:
        # Max 5 MB = 5 * 1024 * 1024 bytes
        if reference_image.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Image file must be under 5 MB.'}, status=400)
        content_type = getattr(reference_image, 'content_type', '')
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
        if content_type and content_type.lower() not in allowed_types:
            return JsonResponse({'success': False, 'error': 'Only JPG, PNG, and WebP images are allowed.'}, status=400)

    prompt_req = PromptRequest.objects.create(
        text=text,
        name_or_handle=name_or_handle,
        reference_link=reference_link or None,
        reference_image=reference_image,
        ip_address=ip,
        status='new'
    )

    return JsonResponse({
        'success': True,
        'message': 'Your prompt request has been dropped into the box! Only @aswinthefilmer can see it.'
    })


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /api/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    """Dynamic XML sitemap listing home and published prompt pages."""
    prompts = Prompt.published.all().order_by('-publish_at')
    categories = Category.objects.all()
    
    items = []
    base_url = request.build_absolute_uri('/')[:-1]
    
    # Homepage
    items.append({
        'loc': f"{base_url}/",
        'lastmod': timezone.now().strftime("%Y-%m-%d"),
        'changefreq': 'daily',
        'priority': '1.0'
    })
    
    # Prompts
    for p in prompts:
        items.append({
            'loc': f"{base_url}{p.get_absolute_url()}",
            'lastmod': p.updated_at.strftime("%Y-%m-%d"),
            'changefreq': 'weekly',
            'priority': '0.8'
        })
        
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>',
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for item in items:
        xml_content.append('  <url>')
        xml_content.append(f"    <loc>{item['loc']}</loc>")
        xml_content.append(f"    <lastmod>{item['lastmod']}</lastmod>")
        xml_content.append(f"    <changefreq>{item['changefreq']}</changefreq>")
        xml_content.append(f"    <priority>{item['priority']}</priority>")
        xml_content.append('  </url>')
    xml_content.append('</urlset>')
    
    return HttpResponse("\n".join(xml_content), content_type="application/xml")
