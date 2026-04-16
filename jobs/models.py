from django.db import models
from django.contrib.auth.models import AbstractUser


# ─── Custom User ───────────────────────────────────────────
class User(AbstractUser):
    ROLE_CHOICES = (
        ('seeker',   'Job Seeker'),
        ('employer', 'Employer'),
    )
    role  = models.CharField(max_length=20, choices=ROLE_CHOICES, default='seeker')
    phone = models.CharField(max_length=20, blank=True)

    def is_employer(self):
        return self.role == 'employer'

    def is_seeker(self):
        return self.role == 'seeker'
    
# ─── Resume Builder ──────────────────────────────────────────
class ResumeBuilder(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume_builder')
    full_name   = models.CharField(max_length=255)
    email       = models.EmailField()
    phone       = models.CharField(max_length=20, blank=True)
    location    = models.CharField(max_length=200, blank=True)
    summary     = models.TextField(blank=True)
    skills      = models.TextField(blank=True, help_text="Comma separated: Python, Django, SQL")
    experience  = models.TextField(blank=True, help_text="JSON format")
    education   = models.TextField(blank=True, help_text="JSON format")
    linkedin    = models.URLField(blank=True)
    github      = models.URLField(blank=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def get_skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def __str__(self):
        return f"{self.user.username}'s Resume"


# ─── Chat ────────────────────────────────────────────────────
class ChatRoom(models.Model):
    application = models.OneToOneField('Application', on_delete=models.CASCADE, related_name='chat_room')
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat: {self.application}"

class ChatMessage(models.Model):
    room      = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender    = models.ForeignKey(User, on_delete=models.CASCADE)
    message   = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"


# ─── Job Bookmark ────────────────────────────────────────────
class SavedJob(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')


# ─── Job Category ───────────────────────────────────────────
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


# ─── Job Listing ────────────────────────────────────────────
class Job(models.Model):
    JOB_TYPE_CHOICES = (
        ('full_time',  'Full Time'),
        ('part_time',  'Part Time'),
        ('remote',     'Remote'),
        ('contract',   'Contract'),
        ('internship', 'Internship'),
    )
    STATUS_CHOICES = (
        ('open',   'Open'),
        ('closed', 'Closed'),
    )

    employer     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    category     = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    title        = models.CharField(max_length=255)
    company      = models.CharField(max_length=255)
    location     = models.CharField(max_length=255)
    job_type     = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    description  = models.TextField()
    requirements = models.TextField()
    salary       = models.CharField(max_length=100, blank=True)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ['-created_at']


# ─── Resume ─────────────────────────────────────────────────
class Resume(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title       = models.CharField(max_length=255)
    file        = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


# ─── Application ────────────────────────────────────────────
class Application(models.Model):
    STATUS_CHOICES = (
        ('pending',      'Pending'),
        ('reviewing',    'Reviewing'),
        ('shortlisted',  'Shortlisted'),
        ('rejected',     'Rejected'),
        ('hired',        'Hired'),
    )

    job          = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    resume       = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'applicant')
        ordering        = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} → {self.job.title}"