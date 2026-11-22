import csv
import datetime
from zoneinfo import ZoneInfo
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Sum

from core.models import SiteSettings
from prompts.models import Prompt, Category, PromptLike, get_default_publish_time
from requests_app.models import PromptRequest


def is_influencer_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_overview(request):
    """Main overview dashboard with stats, upcoming drops queue, and recent requests."""
    now = timezone.now()
    
    total_prompts = Prompt.objects.count()
    live_prompts = Prompt.published.count()
    scheduled_prompts = Prompt.objects.filter(is_published=True, publish_at__gt=now).order_by('publish_at')
    
    # Calculate total likes: sum of like_count + PromptLike count
    base_likes = Prompt.objects.aggregate(total=Sum('like_count'))['total'] or 0
    real_likes = PromptLike.objects.count()
    total_likes = base_likes + real_likes
    
    new_requests = PromptRequest.objects.filter(status='new').count()
    total_requests = PromptRequest.objects.count()
    
    settings = SiteSettings.load()
    today_unlocks = settings.today_unlocked_count
    
    recent_requests = PromptRequest.objects.all().order_by('-created_at')[:6]
    recent_prompts = Prompt.objects.all().select_related('category').order_by('-created_at')[:8]

    context = {
        'total_prompts': total_prompts,
        'live_prompts': live_prompts,
        'scheduled_count': scheduled_prompts.count(),
        'scheduled_prompts': scheduled_prompts[:5],
        'total_likes': total_likes,
        'new_requests': new_requests,
        'total_requests': total_requests,
        'today_unlocks': today_unlocks,
        'recent_requests': recent_requests,
        'recent_prompts': recent_prompts,
        'active_tab': 'overview',
    }
    return render(request, 'dashboard/overview.html', context)


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_prompts_list(request):
    """Manage all prompts with status filter, quick actions, and mobile card view."""
    now = timezone.now()
    status_filter = request.GET.get('status', 'all')
    prompts = Prompt.objects.all().select_related('category')
    
    if status_filter == 'live':
        prompts = prompts.filter(is_published=True, publish_at__lte=now)
    elif status_filter == 'scheduled':
        prompts = prompts.filter(is_published=True, publish_at__gt=now)
    elif status_filter == 'draft':
        prompts = prompts.filter(is_published=False)
        
    context = {
        'prompts': prompts,
        'status_filter': status_filter,
        'active_tab': 'prompts',
    }
    return render(request, 'dashboard/prompts_list.html', context)


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_prompt_add(request):
    """Add a new prompt with file uploads, drop scheduling, and secret prompt text."""
    categories = Category.objects.all()
    default_drop = get_default_publish_time()
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        prompt_type = request.POST.get('type', 'image')
        prompt_text = request.POST.get('prompt_text', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        like_count = request.POST.get('like_count', '0')
        is_published = request.POST.get('is_published') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        publish_at_str = request.POST.get('publish_at', '').strip()
        
        cover_image = request.FILES.get('cover_image')
        before_image = request.FILES.get('before_image')
        after_image = request.FILES.get('after_image')
        video_file = request.FILES.get('video_file')
        
        if not title or not category_id or not prompt_text:
            messages.error(request, "Title, Category, and Prompt Text are required.")
            return render(request, 'dashboard/prompt_form.html', {
                'categories': categories,
                'default_drop': default_drop.strftime("%Y-%m-%dT%H:%M"),
                'is_edit': False,
            })
            
        category = get_object_or_404(Category, id=category_id)
        
        publish_at = default_drop
        if publish_at_str:
            try:
                # Expecting HTML datetime-local format: YYYY-MM-DDTHH:MM
                dt = datetime.datetime.fromisoformat(publish_at_str)
                ist = ZoneInfo("Asia/Kolkata")
                publish_at = dt.replace(tzinfo=ist)
            except Exception:
                publish_at = default_drop

        prompt = Prompt.objects.create(
            title=title,
            category=category,
            type=prompt_type,
            prompt_text=prompt_text,
            cover_image=cover_image,
            before_image=before_image,
            after_image=after_image,
            video_url=video_url or None,
            video_file=video_file,
            like_count=int(like_count) if like_count.isdigit() else 0,
            is_published=is_published,
            publish_at=publish_at,
            is_featured=is_featured,
        )
        messages.success(request, f"Prompt '{prompt.title}' created successfully!")
        return redirect('dashboard:prompts_list')

    context = {
        'categories': categories,
        'default_drop': default_drop.strftime("%Y-%m-%dT%H:%M"),
        'is_edit': False,
        'active_tab': 'prompts',
    }
    return render(request, 'dashboard/prompt_form.html', context)


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_prompt_edit(request, prompt_id):
    """Edit existing prompt."""
    prompt = get_object_or_404(Prompt, id=prompt_id)
    categories = Category.objects.all()
    ist = ZoneInfo("Asia/Kolkata")
    
    if request.method == 'POST':
        prompt.title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        prompt.type = request.POST.get('type', 'image')
        prompt.prompt_text = request.POST.get('prompt_text', '').strip()
        prompt.video_url = request.POST.get('video_url', '').strip() or None
        
        like_count = request.POST.get('like_count', '0')
        prompt.like_count = int(like_count) if like_count.isdigit() else 0
        prompt.is_published = request.POST.get('is_published') == 'on'
        prompt.is_featured = request.POST.get('is_featured') == 'on'
        
        publish_at_str = request.POST.get('publish_at', '').strip()
        if publish_at_str:
            try:
                dt = datetime.datetime.fromisoformat(publish_at_str)
                prompt.publish_at = dt.replace(tzinfo=ist)
            except Exception:
                pass
                
        if request.FILES.get('cover_image'):
            prompt.cover_image = request.FILES.get('cover_image')
        if request.FILES.get('before_image'):
            prompt.before_image = request.FILES.get('before_image')
        if request.FILES.get('after_image'):
            prompt.after_image = request.FILES.get('after_image')
        if request.FILES.get('video_file'):
            prompt.video_file = request.FILES.get('video_file')
            
        if category_id:
            prompt.category = get_object_or_404(Category, id=category_id)
            
        prompt.save()
        messages.success(request, f"Prompt '{prompt.title}' updated successfully!")
        return redirect('dashboard:prompts_list')

    # Convert publish_at to local IST string for datetime-local input
    publish_at_local = prompt.publish_at.astimezone(ist).strftime("%Y-%m-%dT%H:%M") if prompt.publish_at else ""

    context = {
        'prompt': prompt,
        'categories': categories,
        'publish_at_local': publish_at_local,
        'is_edit': True,
        'active_tab': 'prompts',
    }
    return render(request, 'dashboard/prompt_form.html', context)


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_prompt_delete(request, prompt_id):
    prompt = get_object_or_404(Prompt, id=prompt_id)
    if request.method == 'POST':
        title = prompt.title
        prompt.delete()
        messages.success(request, f"Prompt '{title}' deleted.")
        return redirect('dashboard:prompts_list')
    return render(request, 'dashboard/prompt_confirm_delete.html', {'prompt': prompt})


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_prompt_publish_now(request, prompt_id):
    prompt = get_object_or_404(Prompt, id=prompt_id)
    if request.method == 'POST':
        prompt.is_published = True
        prompt.publish_at = timezone.now()
        prompt.save()
        messages.success(request, f"'{prompt.title}' published live immediately!")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:prompts_list'))


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_requests_list(request):
    """View and manage prompt requests with status filter and CSV export."""
    status_filter = request.GET.get('status', 'all')
    requests = PromptRequest.objects.all()
    if status_filter in ['new', 'seen', 'done']:
        requests = requests.filter(status=status_filter)
        
    context = {
        'requests': requests,
        'status_filter': status_filter,
        'active_tab': 'requests',
    }
    return render(request, 'dashboard/requests_list.html', context)


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_request_mark_done(request, request_id):
    req = get_object_or_404(PromptRequest, id=request_id)
    if request.method == 'POST':
        req.status = 'done'
        req.save()
        messages.success(request, f"Request marked as done.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:requests_list'))


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_export_requests_csv(request):
    """Export all prompt requests to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="prompt_requests_{timezone.now().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Status', 'Name/Handle', 'Request Text', 'Reference Link', 'Has Image', 'IP Address', 'Created At'])
    for r in PromptRequest.objects.all().order_by('-created_at'):
        writer.writerow([
            r.id,
            r.status,
            r.name_or_handle or 'Anonymous',
            r.text,
            r.reference_link or '',
            'Yes' if r.reference_image else 'No',
            r.ip_address or '',
            r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    return response


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_settings_view(request):
    """Edit SiteSettings (YouTube link, unlocked base number, drop time, etc.)."""
    settings = SiteSettings.load()
    if request.method == 'POST':
        settings.youtube_channel_url = request.POST.get('youtube_channel_url', '').strip()
        settings.instagram_url = request.POST.get('instagram_url', '').strip()
        settings.whatsapp_url = request.POST.get('whatsapp_url', '').strip()
        
        base_unlocks = request.POST.get('unlocked_today_base', '2243')
        if base_unlocks.isdigit():
            settings.unlocked_today_base = int(base_unlocks)
            
        drop_time = request.POST.get('daily_drop_time', '18:00').strip()
        if drop_time:
            settings.daily_drop_time = drop_time
            
        settings.save()
        messages.success(request, "Site settings updated successfully!")
        return redirect('dashboard:settings')

    context = {
        'settings': settings,
        'active_tab': 'settings',
    }
    return render(request, 'dashboard/settings.html', context)


@user_passes_test(is_influencer_admin, login_url='/admin/login/')
def dashboard_categories_view(request):
    """Manage categories (Portrait, Couple Prompts, Festive, Birthday, Cinematic, General, Stories, Surreal)."""
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        order = request.POST.get('order', '0')
        if name:
            Category.objects.create(name=name, order=int(order) if order.isdigit() else 0)
            messages.success(request, f"Category '{name}' created!")
            return redirect('dashboard:categories')

    context = {
        'categories': categories,
        'active_tab': 'categories',
    }
    return render(request, 'dashboard/categories.html', context)
