from django.test import TestCase, Client
from django.contrib.auth.models import User
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
