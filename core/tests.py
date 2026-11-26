from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.conf import settings
from core.models import SiteSettings
from prompts.models import Category, Prompt
from requests_app.models import PromptRequest


class DashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser('influencer', 'aswin@example.com', 'pass1234')
        self.category = Category.objects.create(name='Portrait', order=1)
        self.prompt = Prompt.objects.create(
            title='Test Dashboard Prompt',
            category=self.category,
            prompt_text='Secret text',
            is_published=False
        )
        self.request_obj = PromptRequest.objects.create(
            text='Test requested prompt',
            name_or_handle='Fan123',
            status='new'
        )

    def test_dashboard_login_protection(self):
        """Anonymous visitor redirected to login."""
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login/', resp.url)

    def test_dashboard_accessible_to_influencer(self):
        """Logged in influencer can access dashboard overview."""
        self.client.login(username='influencer', password='pass1234')
        resp = self.client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('CREATOR OVERVIEW', resp.content.decode())

    def test_dashboard_csv_export(self):
        """CSV export returns proper attachment and headers."""
        self.client.login(username='influencer', password='pass1234')
        resp = self.client.get('/dashboard/requests/export-csv/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')
        content = resp.content.decode()
        self.assertIn('ID,Status,Name/Handle,Request Text', content)
        self.assertIn('Fan123', content)

    def test_dashboard_mark_request_done(self):
        """Mark as done updates status."""
        self.client.login(username='influencer', password='pass1234')
        resp = self.client.post(f'/dashboard/requests/{self.request_obj.id}/done/')
        self.assertEqual(resp.status_code, 302)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, 'done')


class RailwayCSRFConfigurationTests(TestCase):
    def test_settings_trusted_origins_and_hosts(self):
        """Verify ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS contain Railway production URL without wildcards."""
        self.assertIn('promptrepo-production.up.railway.app', settings.ALLOWED_HOSTS)
        self.assertIn('https://promptrepo-production.up.railway.app', settings.CSRF_TRUSTED_ORIGINS)
        
        # Verify no wildcards in CSRF_TRUSTED_ORIGINS
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            self.assertNotIn('*', origin, f"Wildcard found in trusted origin: {origin}")

        # Verify reverse proxy header is set
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, ('HTTP_X_FORWARDED_PROTO', 'https'))

        # Verify CSRF middleware is in MIDDLEWARE
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)

    def test_railway_origin_passes_csrf(self):
        """Verify POST request with Railway origin and CSRF cookie passes CSRF check."""
        client = Client(enforce_csrf_checks=True)
        
        # 1. First get the CSRF cookie by visiting home
        home_resp = client.get('/', HTTP_HOST='promptrepo-production.up.railway.app', HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(home_resp.status_code, 200)
        csrf_token = home_resp.cookies['csrftoken'].value

        # 2. Perform a POST request mimicking the Railway HTTPS environment
        post_resp = client.post(
            '/api/unlock/',
            data={},
            HTTP_HOST='promptrepo-production.up.railway.app',
            HTTP_ORIGIN='https://promptrepo-production.up.railway.app',
            HTTP_X_FORWARDED_PROTO='https',
            HTTP_X_CSRFTOKEN=csrf_token,
            content_type='application/json'
        )
        # Should succeed with 200 OK (NOT 403 Forbidden Origin checking failed)
        self.assertEqual(post_resp.status_code, 200)
        self.assertTrue(post_resp.json().get('success'))

    def test_untrusted_origin_rejected_by_csrf(self):
        """Verify untrusted origin is rejected with 403 Forbidden."""
        client = Client(enforce_csrf_checks=True)
        home_resp = client.get('/', HTTP_HOST='promptrepo-production.up.railway.app', HTTP_X_FORWARDED_PROTO='https')
        csrf_token = home_resp.cookies['csrftoken'].value

        post_resp = client.post(
            '/api/unlock/',
            data={},
            HTTP_HOST='promptrepo-production.up.railway.app',
            HTTP_ORIGIN='https://untrusted-external-site.com',
            HTTP_X_FORWARDED_PROTO='https',
            HTTP_X_CSRFTOKEN=csrf_token,
            content_type='application/json'
        )
        self.assertEqual(post_resp.status_code, 403)
