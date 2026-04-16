from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
import json

from .models import Job, Application, Resume, ChatRoom, ChatMessage, Category, SavedJob, ResumeBuilder
from .forms import JobForm, ResumeUploadForm, RegisterForm, ApplicationForm, ResumeBuilderForm


# ══════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════

def register(request):
    """
    BUG FIX: was using Django's generic UserCreationForm — role was never saved.
    Now uses custom RegisterForm which includes the role field.
    """
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.username}! Your account has been created.")
        return redirect('home')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = AuthenticationForm(request, data=request.POST or None)
    if form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get('next', 'home')
        messages.success(request, f"Welcome back, {form.get_user().username}!")
        return redirect(next_url)
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ══════════════════════════════════════════════
#  HOME — search, filter, pagination
# ══════════════════════════════════════════════

def home(request):
    """
    BUG FIX: view was returning a plain QuerySet — home.html expects a
    paginated Page object (jobs.paginator.count, jobs.has_other_pages etc.)
    and also expects 'keyword', 'location', 'categories' in context.
    """
    keyword  = request.GET.get('keyword', '').strip()
    location = request.GET.get('location', '').strip()
    cat_id   = request.GET.get('category', '')
    job_type = request.GET.get('job_type', '')

    jobs = Job.objects.filter(status='open').select_related('category', 'employer')

    if keyword:
        jobs = jobs.filter(
            Q(title__icontains=keyword) |
            Q(company__icontains=keyword) |
            Q(description__icontains=keyword)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if cat_id:
        jobs = jobs.filter(category_id=cat_id)
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    paginator = Paginator(jobs, 10)
    page      = request.GET.get('page', 1)
    jobs      = paginator.get_page(page)

    # Saved job IDs for the current user (to show bookmark state)
    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(
            SavedJob.objects.filter(user=request.user).values_list('job_id', flat=True)
        )

    context = {
        'jobs':       jobs,
        'categories': Category.objects.all(),
        'keyword':    keyword,
        'location':   location,
        'saved_ids':  saved_ids,
    }
    return render(request, 'home.html', context)


# ══════════════════════════════════════════════
#  JOB CRUD
# ══════════════════════════════════════════════

def job_detail(request, pk):
    job        = get_object_or_404(Job, pk=pk)
    has_applied = False
    is_saved    = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(job=job, applicant=request.user).exists()
        is_saved    = SavedJob.objects.filter(job=job, user=request.user).exists()
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'has_applied': has_applied,
        'is_saved': is_saved,
    })


@login_required
def post_job(request):
    if not request.user.is_employer():
        messages.error(request, "Only employers can post jobs.")
        return redirect('home')
    form = JobForm(request.POST or None)
    if form.is_valid():
        job          = form.save(commit=False)
        job.employer = request.user
        job.save()
        messages.success(request, "Job posted successfully!")
        return redirect('employer_dashboard')
    return render(request, 'jobs/post_job.html', {'form': form, 'action': 'Post'})


@login_required
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    form = JobForm(request.POST or None, instance=job)
    if form.is_valid():
        form.save()
        messages.success(request, "Job updated successfully!")
        return redirect('employer_dashboard')
    return render(request, 'jobs/post_job.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_job(request, pk):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted.")
    return redirect('employer_dashboard')


# ══════════════════════════════════════════════
#  APPLICATIONS
# ══════════════════════════════════════════════

@login_required
def apply_job(request, pk):
    """
    BUG FIX: was using get_or_create directly — skipped resume & cover letter.
    Now uses ApplicationForm so seeker can attach a resume and write a cover letter.
    """
    job = get_object_or_404(Job, pk=pk, status='open')

    if request.user.is_employer():
        messages.error(request, "Employers cannot apply for jobs.")
        return redirect('job_detail', pk=pk)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect('job_detail', pk=pk)

    form = ApplicationForm(request.POST or None, user=request.user)
    if form.is_valid():
        app           = form.save(commit=False)
        app.job       = job
        app.applicant = request.user
        app.save()
        messages.success(request, f"Applied to {job.title} successfully!")
        return redirect('my_applications')

    return render(request, 'applications/apply.html', {'form': form, 'job': job})


@login_required
def my_applications(request):
    apps = (Application.objects
            .filter(applicant=request.user)
            .select_related('job', 'job__employer')
            .order_by('-applied_at'))
    return render(request, 'applications/my_applications.html', {'applications': apps})


@login_required
def update_status(request, pk):
    app = get_object_or_404(Application, pk=pk, job__employer=request.user)
    new_status = request.POST.get('status')
    valid = [s[0] for s in Application.STATUS_CHOICES]
    if new_status in valid:
        app.status = new_status
        app.save()
        messages.success(request, f"Status updated to {new_status}.")
    return redirect('employer_dashboard')


# ══════════════════════════════════════════════
#  BOOKMARK / SAVE JOB
# ══════════════════════════════════════════════

@login_required
def toggle_save_job(request, pk):
    """
    NEW: SavedJob model existed but had no view/URL.
    Toggles bookmark; returns JSON for AJAX or redirects for plain requests.
    """
    job  = get_object_or_404(Job, pk=pk)
    obj, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        obj.delete()
        saved = False
    else:
        saved = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'saved': saved})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def saved_jobs(request):
    saves = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')
    return render(request, 'jobs/saved_jobs.html', {'saves': saves})


# ══════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════

@login_required
def employer_dashboard(request):
    if not request.user.is_employer():
        return redirect('home')
    jobs = (Job.objects
            .filter(employer=request.user)
            .annotate(app_count=Count('applications'))
            .order_by('-created_at'))
    return render(request, 'jobs/employer_dashboard.html', {'jobs': jobs})


# ══════════════════════════════════════════════
#  ANALYTICS
# ══════════════════════════════════════════════

@login_required
def analytics_dashboard(request):
    if request.user.is_employer():
        jobs        = Job.objects.filter(employer=request.user)
        apps_per_job = list(
            jobs.annotate(app_count=Count('applications'))
            .values('title', 'app_count')
        )
        status_data = list(
            Application.objects.filter(job__employer=request.user)
            .values('status').annotate(count=Count('id'))
        )
        daily_apps = list(
            Application.objects
            .filter(job__employer=request.user)
            .annotate(date=TruncDate('applied_at'))
            .values('date').annotate(count=Count('id'))
            .order_by('date')
        )
        context = {
            'is_employer': True,
            'apps_per_job': json.dumps(apps_per_job, default=str),
            'status_data':  json.dumps(status_data),
            'daily_apps':   json.dumps(daily_apps, default=str),
            'total_jobs':   jobs.count(),
            'total_apps':   Application.objects.filter(job__employer=request.user).count(),
            'open_jobs':    jobs.filter(status='open').count(),
        }
    else:
        apps        = Application.objects.filter(applicant=request.user)
        status_data = list(apps.values('status').annotate(count=Count('id')))
        context = {
            'is_employer':  False,
            'status_data':  json.dumps(status_data),
            'total_apps':   apps.count(),
            'pending_apps': apps.filter(status='pending').count(),
            'hired_apps':   apps.filter(status='hired').count(),
        }
    return render(request, 'jobs/analytics.html', context)


# ══════════════════════════════════════════════
#  RESUME UPLOAD
# ══════════════════════════════════════════════

@login_required
def upload_resume(request):
    form = ResumeUploadForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        resume      = form.save(commit=False)
        resume.user = request.user
        resume.save()
        messages.success(request, "Resume uploaded successfully!")
        return redirect('my_applications')
    return render(request, 'jobs/upload_resume.html', {'form': form})


# ══════════════════════════════════════════════
#  RESUME BUILDER
# ══════════════════════════════════════════════

@login_required
def resume_builder(request):
    """
    BUG FIX: was a stub. Now saves/loads from the ResumeBuilder model.
    """
    instance, _ = ResumeBuilder.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.get_full_name() or request.user.username,
            'email':     request.user.email,
        }
    )
    form = ResumeBuilderForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, "Resume saved!")
        return redirect('resume_builder')
    return render(request, 'resume/builder.html', {'form': form, 'resume': instance})


@login_required
def export_resume_pdf(request):
    """
    BUG FIX: was a stub. Now generates a real PDF using ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        from io import BytesIO
        import json as _json
    except ImportError:
        messages.error(request, "PDF generation requires 'reportlab'. Install it with: pip install reportlab")
        return redirect('resume_builder')

    try:
        rb = request.user.resume_builder
    except ResumeBuilder.DoesNotExist:
        messages.warning(request, "Please fill in your Resume Builder profile first.")
        return redirect('resume_builder')

    buf    = BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # Title
    story.append(Paragraph(rb.full_name, ParagraphStyle('title',
        fontSize=22, fontName='Helvetica-Bold', spaceAfter=4)))
    contact = " | ".join(filter(None, [rb.email, rb.phone, rb.location,
                                        rb.linkedin, rb.github]))
    if contact:
        story.append(Paragraph(contact, ParagraphStyle('contact',
            fontSize=9, textColor=colors.grey, spaceAfter=6)))
    story.append(HRFlowable(width='100%', thickness=1.5,
                             color=colors.HexColor('#0d6efd'), spaceAfter=10))

    def section(title):
        story.append(Spacer(1, 6))
        story.append(Paragraph(title, ParagraphStyle('sec',
            fontSize=12, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0d6efd'), spaceAfter=4)))
        story.append(HRFlowable(width='100%', thickness=0.5,
                                 color=colors.lightgrey, spaceAfter=6))

    if rb.summary:
        section("Professional Summary")
        story.append(Paragraph(rb.summary, styles['Normal']))

    if rb.skills:
        section("Skills")
        skill_text = "  •  ".join(rb.get_skills_list())
        story.append(Paragraph(skill_text, styles['Normal']))

    if rb.experience:
        section("Experience")
        try:
            exps = _json.loads(rb.experience)
            for exp in exps:
                story.append(Paragraph(
                    f"<b>{exp.get('role','')}</b> — {exp.get('company','')}  "
                    f"<font color='grey'>{exp.get('duration','')}</font>",
                    styles['Normal']))
                if exp.get('description'):
                    story.append(Paragraph(exp['description'],
                        ParagraphStyle('desc', leftIndent=10, spaceAfter=4,
                                       fontSize=9, textColor=colors.grey)))
        except Exception:
            story.append(Paragraph(rb.experience, styles['Normal']))

    if rb.education:
        section("Education")
        try:
            edus = _json.loads(rb.education)
            for edu in edus:
                story.append(Paragraph(
                    f"<b>{edu.get('degree','')}</b> — {edu.get('institution','')}  "
                    f"<font color='grey'>{edu.get('year','')}</font>",
                    styles['Normal']))
        except Exception:
            story.append(Paragraph(rb.education, styles['Normal']))

    doc.build(story)
    buf.seek(0)
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{rb.full_name}_resume.pdf"'
    return response


# ══════════════════════════════════════════════
#  JOB RECOMMENDATIONS
# ══════════════════════════════════════════════

@login_required
def job_recommendations(request):
    """
    BUG FIX: was a stub.
    Simple keyword-based recommendations: match jobs whose title/description
    overlaps with skills from the user's ResumeBuilder or previous applications.
    """
    recommended = Job.objects.none()
    reason      = ""

    # 1. Try to match via ResumeBuilder skills
    try:
        rb     = request.user.resume_builder
        skills = rb.get_skills_list()
        if skills:
            q = Q()
            for skill in skills:
                q |= Q(title__icontains=skill) | Q(description__icontains=skill)
            recommended = Job.objects.filter(q, status='open').distinct()
            reason = f"Based on your skills: {', '.join(skills[:5])}"
    except ResumeBuilder.DoesNotExist:
        pass

    # 2. Fallback: match based on categories of past applications
    if not recommended.exists():
        past_cats = (Application.objects
                     .filter(applicant=request.user)
                     .values_list('job__category_id', flat=True)
                     .distinct())
        if past_cats:
            recommended = Job.objects.filter(
                category_id__in=past_cats, status='open'
            ).exclude(
                id__in=Application.objects.filter(applicant=request.user).values('job_id')
            )
            reason = "Based on your previous applications"

    # 3. Fallback: latest open jobs
    if not recommended.exists():
        recommended = Job.objects.filter(status='open')
        reason = "Latest open positions"

    recommended = recommended.select_related('category')[:20]
    return render(request, 'jobs/recommendations.html', {
        'recommended': recommended,
        'reason': reason,
    })


# ══════════════════════════════════════════════
#  CHAT
# ══════════════════════════════════════════════

@login_required
def start_chat(request, application_id):
    app = get_object_or_404(Application, id=application_id)
    # Only the applicant or the employer can open the chat
    if request.user not in (app.applicant, app.job.employer):
        messages.error(request, "Access denied.")
        return redirect('home')
    room, _ = ChatRoom.objects.get_or_create(application=app)
    return redirect('chat_room', room_id=room.id)


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    # Access check
    if request.user not in (room.application.applicant, room.application.job.employer):
        messages.error(request, "Access denied.")
        return redirect('home')
    messages_qs = room.messages.select_related('sender').order_by('timestamp')
    # Mark unread messages as read
    messages_qs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'chat/room.html', {
        'room_id':  room_id,
        'room':     room,
        'chat_messages': messages_qs,
    })


# ══════════════════════════════════════════════
#  PDF EXPORTS
# ══════════════════════════════════════════════

@login_required
def export_applications_pdf(request):
    """
    BUG FIX: was a stub. Generates a real PDF of all applications.
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import cm
        from io import BytesIO
    except ImportError:
        messages.error(request, "PDF generation requires 'reportlab'.")
        return redirect('my_applications')

    if request.user.is_employer():
        apps = Application.objects.filter(
            job__employer=request.user
        ).select_related('job', 'applicant').order_by('-applied_at')
        filename = "employer_applications.pdf"
    else:
        apps = Application.objects.filter(
            applicant=request.user
        ).select_related('job').order_by('-applied_at')
        filename = f"{request.user.username}_applications.pdf"

    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=landscape(A4),
                              leftMargin=1.5*cm, rightMargin=1.5*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    story.append(Paragraph("Applications Report", styles['Title']))
    story.append(Paragraph(
        f"Generated: {timezone.now().strftime('%d %b %Y %H:%M')}",
        styles['Normal']))
    story.append(Spacer(1, 12))

    headers = ['#', 'Job Title', 'Company', 'Applicant', 'Status', 'Applied At']
    rows    = [headers]
    for i, app in enumerate(apps, 1):
        rows.append([
            str(i),
            app.job.title,
            app.job.company,
            app.applicant.username if request.user.is_employer() else request.user.username,
            app.status.capitalize(),
            app.applied_at.strftime('%d/%m/%Y'),
        ])

    STATUS_COLOR = {
        'pending':     colors.orange,
        'reviewing':   colors.blue,
        'shortlisted': colors.green,
        'rejected':    colors.red,
        'hired':       colors.darkgreen,
    }

    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f4ff')]),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.lightgrey),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING',    (0,0), (-1,-1), 6),
    ]))
    story.append(table)
    doc.build(story)

    buf.seek(0)
    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp