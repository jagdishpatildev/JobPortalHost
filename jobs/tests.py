"""
BUG FIX: the original tests.py had full model class definitions pasted
at the top of the file, which shadowed the real imports from .models.
Removed those duplicate definitions.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Job, Application, ResumeBuilder, Category

User = get_user_model()


class HireHubTestCase(TestCase):
    def setUp(self):
        self.client   = Client()
        self.seeker   = User.objects.create_user(
            username='seeker1', password='pass123', role='seeker')
        self.employer = User.objects.create_user(
            username='employer1', password='pass123', role='employer')
        self.category = Category.objects.create(name='Engineering')
        self.job = Job.objects.create(
            employer    = self.employer,
            title       = 'Backend Developer',
            company     = 'TechCorp',
            location    = 'Pune',
            description = 'Build APIs',
            requirements= 'Python, Django',
            category    = self.category,
        )

    # ── Model tests ──────────────────────────────────────────
    def test_job_creation(self):
        self.assertEqual(self.job.title, 'Backend Developer')
        self.assertEqual(str(self.job), 'Backend Developer at TechCorp')

    def test_user_roles(self):
        self.assertTrue(self.seeker.is_seeker())
        self.assertFalse(self.seeker.is_employer())
        self.assertTrue(self.employer.is_employer())
        self.assertFalse(self.employer.is_seeker())

    # ── Auth tests ───────────────────────────────────────────
    def test_register_page_loads(self):
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)

    def test_login_page_loads(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

    def test_login_success(self):
        resp = self.client.post(reverse('login'), {
            'username': 'seeker1',
            'password': 'pass123',
        })
        self.assertRedirects(resp, reverse('home'))

    # ── Home / search tests ──────────────────────────────────
    def test_home_loads(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('jobs', resp.context)

    def test_home_search_keyword(self):
        resp = self.client.get(reverse('home'), {'keyword': 'Backend'})
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.context['jobs'].paginator.count, 1)

    def test_home_search_no_results(self):
        resp = self.client.get(reverse('home'), {'keyword': 'QuantumPhysicistXYZ'})
        self.assertEqual(resp.context['jobs'].paginator.count, 0)

    # ── Job detail test ──────────────────────────────────────
    def test_job_detail_loads(self):
        resp = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertEqual(resp.status_code, 200)

    # ── Post job (employer only) ─────────────────────────────
    def test_post_job_requires_login(self):
        resp = self.client.get(reverse('post_job'))
        self.assertEqual(resp.status_code, 302)   # redirect to login

    def test_seeker_cannot_post_job(self):
        self.client.login(username='seeker1', password='pass123')
        resp = self.client.get(reverse('post_job'))
        self.assertRedirects(resp, reverse('home'))

    # ── Application tests ────────────────────────────────────
    def test_apply_requires_login(self):
        resp = self.client.get(reverse('apply_job', args=[self.job.pk]))
        self.assertEqual(resp.status_code, 302)

    def test_application_created(self):
        self.client.login(username='seeker1', password='pass123')
        self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'I am a great fit!',
        })
        self.assertTrue(
            Application.objects.filter(job=self.job, applicant=self.seeker).exists()
        )

    def test_duplicate_application_blocked(self):
        Application.objects.create(job=self.job, applicant=self.seeker)
        self.client.login(username='seeker1', password='pass123')
        self.client.post(reverse('apply_job', args=[self.job.pk]), {
            'cover_letter': 'Applying again',
        })
        self.assertEqual(
            Application.objects.filter(job=self.job, applicant=self.seeker).count(), 1
        )

    # ── Resume Builder tests ─────────────────────────────────
    def test_resume_builder_creates_instance(self):
        self.client.login(username='seeker1', password='pass123')
        self.client.get(reverse('resume_builder'))
        self.assertTrue(ResumeBuilder.objects.filter(user=self.seeker).exists())

    # ── Dashboard tests ──────────────────────────────────────
    def test_employer_dashboard_loads(self):
        self.client.login(username='employer1', password='pass123')
        resp = self.client.get(reverse('employer_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('jobs', resp.context)