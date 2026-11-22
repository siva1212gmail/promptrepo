import datetime
from zoneinfo import ZoneInfo
from django.test import TestCase, Client
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import SiteSettings
from prompts.models import Category, Prompt, PromptLike
from requests_app.models import PromptRequest


class PromptPettiSecurityAndApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.settings = SiteSettings.load()
        self.category = Category.objects.create(name="Cinematic", order=1)
        
        # Live prompt
        self.live_prompt = Prompt.objects.create(
            title="Kerala Kathakali Cyberpunk",
            category=self.category,
            type="image",
            prompt_text="TOP_SECRET_PROMPT_TEXT_KATHAKALI_8K",
            like_count=100,
            is_published=True,
            publish_at=timezone.now() - datetime.timedelta(hours=2)
        )

        # Future scheduled prompt (due tomorrow 6 PM)
        self.future_prompt = Prompt.objects.create(
            title="Future Drop Not Yet Live",
            category=self.category,
            type="video",
            prompt_text="FUTURE_SECRET_PROMPT_TEXT",
            like_count=10,
            is_published=True,
            publish_at=timezone.now() + datetime.timedelta(days=1)
        )

    def test_security_rule_prompt_text_never_in_list_api(self):
        """CRITICAL SECURITY: prompt_text must NOT be included in list API."""
        response = self.client.get('/api/prompts/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['results']) >= 1)
        for item in data['results']:
            self.assertNotIn('prompt_text', item)
        self.assertNotIn('TOP_SECRET_PROMPT_TEXT_KATHAKALI_8K', response.content.decode())

    def test_security_rule_prompt_text_never_in_detail_api(self):
        """CRITICAL SECURITY: prompt_text must NOT be in detail API."""
        response = self.client.get(f'/api/prompts/{self.live_prompt.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('prompt_text', data)
        self.assertNotIn('TOP_SECRET_PROMPT_TEXT_KATHAKALI_8K', response.content.decode())

    def test_security_rule_prompt_text_blocked_when_locked(self):
        """GET /api/prompts/<id>/text/ returns 403 Forbidden without unlock."""
        response = self.client.get(f'/api/prompts/{self.live_prompt.id}/text/')
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data.get('error'), 'locked')

    def test_unlock_api_and_text_access(self):
        """POST /api/unlock/ sets cookie and allows access to prompt text."""
        unlock_resp = self.client.post('/api/unlock/')
        self.assertEqual(unlock_resp.status_code, 200)
        self.assertIn('unlocked', unlock_resp.cookies)
        self.assertEqual(unlock_resp.cookies['unlocked'].value, 'true')

        # Now fetching prompt text must succeed
        text_resp = self.client.get(f'/api/prompts/{self.live_prompt.id}/text/')
        self.assertEqual(text_resp.status_code, 200)
        data = text_resp.json()
        self.assertEqual(data.get('prompt_text'), 'TOP_SECRET_PROMPT_TEXT_KATHAKALI_8K')

    def test_future_scheduled_prompt_hidden_from_public(self):
        """Future prompts scheduled after now must not appear on public site or list API."""
        response = self.client.get('/api/prompts/')
        data = response.json()
        titles = [p['title'] for p in data['results']]
        self.assertIn('Kerala Kathakali Cyberpunk', titles)
        self.assertNotIn('Future Drop Not Yet Live', titles)

    def test_like_toggle_api(self):
        """POST /api/prompts/<id>/like/ toggles like count."""
        initial_likes = self.live_prompt.total_likes
        like_resp = self.client.post(f'/api/prompts/{self.live_prompt.id}/like/')
        self.assertEqual(like_resp.status_code, 200)
        data = like_resp.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['total_likes'], initial_likes + 1)

        # Toggle again -> unlike
        unlike_resp = self.client.post(f'/api/prompts/{self.live_prompt.id}/like/')
        self.assertEqual(unlike_resp.status_code, 200)
        data2 = unlike_resp.json()
        self.assertFalse(data2['liked'])
        self.assertEqual(data2['total_likes'], initial_likes)

    def test_prompt_request_form_submission(self):
        """Visitor can submit prompt request without login."""
        post_data = {
            'text': 'Ghibli-style couple photo in Munnar rain',
            'name_or_handle': '@anand_cine',
            'website_url_hp': '',  # Honeypot empty
        }
        resp = self.client.post('/api/requests/', data=post_data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(PromptRequest.objects.filter(name_or_handle='@anand_cine').exists())

    def test_prompt_request_honeypot_spam_trap(self):
        """Honeypot filled must not create a prompt request."""
        post_data = {
            'text': 'Spam test buy crypto',
            'name_or_handle': 'bot',
            'website_url_hp': 'http://spamsite.com',  # Bot filled
        }
        resp = self.client.post('/api/requests/', data=post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(PromptRequest.objects.filter(text='Spam test buy crypto').exists())

    def test_prompt_request_rate_limiting(self):
        """Max 5 requests per IP per hour."""
        for i in range(5):
            r = self.client.post('/api/requests/', {'text': f'Idea {i}', 'name_or_handle': 'User'})
            self.assertEqual(r.status_code, 200)

        # 6th attempt should be blocked
        r6 = self.client.post('/api/requests/', {'text': 'Idea 6th should fail', 'name_or_handle': 'User'})
        self.assertEqual(r6.status_code, 429)

    def test_seo_sitemap_and_robots(self):
        """Verify sitemap.xml and robots.txt exist and return correct content types."""
        robots_resp = self.client.get('/robots.txt')
        self.assertEqual(robots_resp.status_code, 200)
        self.assertIn('User-agent: *', robots_resp.content.decode())

        sitemap_resp = self.client.get('/sitemap.xml')
        self.assertEqual(sitemap_resp.status_code, 200)
        self.assertIn('<urlset', sitemap_resp.content.decode())
        self.assertIn(self.live_prompt.slug, sitemap_resp.content.decode())

    def test_direct_prompt_slug_page_open_graph(self):
        """GET /p/<slug>/ returns server-rendered Open Graph tags and meta viewport."""
        resp = self.client.get(f'/p/{self.live_prompt.slug}/')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('og:title', html)
        self.assertIn('Kerala Kathakali Cyberpunk', html)
        self.assertIn('viewport-fit=cover', html)
