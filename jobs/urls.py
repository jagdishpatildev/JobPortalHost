from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register,      name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),

    # Jobs
    path('',                        views.home,               name='home'),
    path('jobs/<int:pk>/',          views.job_detail,         name='job_detail'),
    path('jobs/post/',              views.post_job,           name='post_job'),
    path('jobs/<int:pk>/edit/',     views.edit_job,           name='edit_job'),
    path('jobs/<int:pk>/delete/',   views.delete_job,         name='delete_job'),
    path('dashboard/',              views.employer_dashboard, name='employer_dashboard'),

    # Bookmarks  ← NEW
    path('jobs/<int:pk>/save/',     views.toggle_save_job,    name='toggle_save_job'),
    path('saved-jobs/',             views.saved_jobs,         name='saved_jobs'),

    # Applications
    path('jobs/<int:pk>/apply/',         views.apply_job,       name='apply_job'),
    path('my-applications/',             views.my_applications, name='my_applications'),
    path('application/<int:pk>/status/', views.update_status,   name='update_status'),

    # Resume Builder
    path('resume/build/',       views.resume_builder,    name='resume_builder'),
    path('resume/export/pdf/',  views.export_resume_pdf, name='export_resume_pdf'),
    path('resume/upload/',      views.upload_resume,     name='upload_resume'),

    # Chat
    path('chat/<int:room_id>/',               views.chat_room,  name='chat_room'),
    path('chat/start/<int:application_id>/',  views.start_chat, name='start_chat'),

    # Recommendations & Analytics
    path('recommendations/', views.job_recommendations,    name='job_recommendations'),
    path('analytics/',       views.analytics_dashboard,    name='analytics_dashboard'),

    # PDF Exports
    path('applications/export/pdf/', views.export_applications_pdf, name='export_applications_pdf'),
]