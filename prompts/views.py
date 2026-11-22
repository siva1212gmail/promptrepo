import uuid
import datetime
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q

from .models import Prompt, Category, PromptLike
from core.views import is_visitor_unlocked, get_client_ip


def get_visitor_id(request):
    """Retrieves or generates a unique visitor ID for like tracking."""
    visitor_id = request.COOKIES.get('visitor_id')
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
    return visitor_id


@require_GET
def api_prompt_list(request):
    """
    GET /api/prompts/?q=&type=&category=&filter=new|liked|all&page=
    CRITICAL SECURITY: prompt_text is NEVER included here!
    """
    now = timezone.now()
    queryset = Prompt.published.all().select_related('category')

    # Query search
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) |
            Q(category__name__icontains=q)
        )

    # Type filter (image / video)
    prompt_type = request.GET.get('type', '').strip()
    if prompt_type in ['image', 'video']:
        queryset = queryset.filter(type=prompt_type)

    # Category filter
    category_slug = request.GET.get('category', '').strip()
    if category_slug and category_slug != 'all':
        queryset = queryset.filter(category__slug=category_slug)

    # Status / filter: new, liked, all
    filter_mode = request.GET.get('filter', '').strip()
    if filter_mode == 'new':
        cutoff = now - datetime.timedelta(hours=24)
        queryset = queryset.filter(publish_at__gte=cutoff)
    elif filter_mode == 'liked':
        # Can filter by passed IDs list from localStorage or visitor_id
        liked_ids_param = request.GET.get('ids', '').strip()
        if liked_ids_param:
            try:
                liked_ids = [int(x) for x in liked_ids_param.split(',') if x.isdigit()]
                queryset = queryset.filter(id__in=liked_ids)
            except Exception:
                pass
        else:
            visitor_id = request.COOKIES.get('visitor_id')
            if visitor_id:
                liked_prompt_ids = PromptLike.objects.filter(visitor_id=visitor_id).values_list('prompt_id', flat=True)
                queryset = queryset.filter(id__in=liked_prompt_ids)
            else:
                queryset = queryset.none()

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(queryset, 12)
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        return JsonResponse({
            'results': [],
            'has_next': False,
            'total_count': paginator.count,
            'page': int(page_number),
            'num_pages': paginator.num_pages,
        })

    results = []
    for p in page_obj:
        results.append({
            'id': p.id,
            'title': p.title,
            'slug': p.slug,
            'type': p.type,
            'type_display': p.get_type_display(),
            'category_name': p.category.name,
            'category_slug': p.category.slug,
            'cover_image_url': p.cover_image.url if p.cover_image else '',
            'has_before_after': p.has_before_after,
            'video_url': p.video_url or '',
            'total_likes': p.total_likes,
            'is_new': p.is_new,
            'detail_url': p.get_absolute_url(),
        })

    return JsonResponse({
        'results': results,
        'has_next': page_obj.has_next(),
        'total_count': paginator.count,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
    })


@require_GET
def api_prompt_detail(request, prompt_id):
    """
    GET /api/prompts/<id>/
    Detail metadata without prompt text. Includes before/after URLs, like count, locked status.
    CRITICAL SECURITY: prompt_text is NOT included!
    """
    # Allowed for live prompts, or staff can preview
    if request.user.is_staff:
        prompt = get_object_or_404(Prompt.objects.select_related('category'), id=prompt_id)
    else:
        prompt = get_object_or_404(Prompt.published.select_related('category'), id=prompt_id)

    unlocked = is_visitor_unlocked(request)
    visitor_id = request.COOKIES.get('visitor_id')
    user_liked = False
    if visitor_id:
        user_liked = PromptLike.objects.filter(prompt=prompt, visitor_id=visitor_id).exists()

    data = {
        'id': prompt.id,
        'title': prompt.title,
        'slug': prompt.slug,
        'type': prompt.type,
        'type_display': prompt.get_type_display(),
        'category_name': prompt.category.name,
        'category_slug': prompt.category.slug,
        'cover_image_url': prompt.cover_image.url if prompt.cover_image else '',
        'before_image_url': prompt.before_image.url if prompt.before_image else '',
        'after_image_url': prompt.after_image.url if prompt.after_image else '',
        'has_before_after': prompt.has_before_after,
        'video_url': prompt.video_url or '',
        'total_likes': prompt.total_likes,
        'user_liked': user_liked,
        'is_new': prompt.is_new,
        'locked': not unlocked,
        'share_url': request.build_absolute_uri(prompt.get_absolute_url()),
    }
    return JsonResponse(data)


@require_GET
def api_prompt_text(request, prompt_id):
    """
    GET /api/prompts/<id>/text/
    CRITICAL SECURITY RULE: Only returns prompt_text when unlocked cookie or session is present!
    Otherwise returns 403 Forbidden.
    """
    if not is_visitor_unlocked(request):
        return JsonResponse({
            'error': 'locked',
            'message': 'Prompt is locked. Tap "I\'m subscribed" after visiting the YouTube channel to unlock.'
        }, status=403)

    if request.user.is_staff:
        prompt = get_object_or_404(Prompt, id=prompt_id)
    else:
        prompt = get_object_or_404(Prompt.published, id=prompt_id)

    return JsonResponse({
        'id': prompt.id,
        'title': prompt.title,
        'prompt_text': prompt.prompt_text,
    })


@require_POST
def api_prompt_like(request, prompt_id):
    """
    POST /api/prompts/<id>/like/
    Toggles like status for this visitor.
    """
    prompt = get_object_or_404(Prompt, id=prompt_id)
    visitor_id = request.COOKIES.get('visitor_id')
    new_visitor = False
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
        new_visitor = True

    ip = get_client_ip(request)

    like_obj = PromptLike.objects.filter(prompt=prompt, visitor_id=visitor_id).first()
    if like_obj:
        # Unlike
        like_obj.delete()
        liked = False
    else:
        # Like
        PromptLike.objects.create(prompt=prompt, visitor_id=visitor_id, ip_address=ip)
        liked = True

    response = JsonResponse({
        'success': True,
        'liked': liked,
        'total_likes': prompt.total_likes,
    })

    if new_visitor:
        response.set_cookie(
            'visitor_id',
            visitor_id,
            max_age=365 * 24 * 60 * 60,
            samesite='Lax'
        )

    return response
