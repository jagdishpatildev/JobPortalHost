from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Job, Category, Application, Resume

admin.site.register(User, UserAdmin)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display  = ('title', 'company', 'location', 'job_type', 'status', 'created_at')
    list_filter   = ('status', 'job_type', 'category')
    search_fields = ('title', 'company', 'location')
    list_editable = ('status',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display  = ('applicant', 'job', 'status', 'applied_at')
    list_filter   = ('status',)
    list_editable = ('status',)

admin.site.register(Category)
admin.site.register(Resume)