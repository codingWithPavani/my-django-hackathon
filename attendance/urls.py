# from django.urls import path
# from . import views

# urlpatterns = [
#     path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),
#     path("teacher/mark-attendance/", views.mark_attendance, name="mark_attendance"),
#     path("teacher/enter-grade/", views.enter_grade, name="enter_grade"),
#     path("student/", views.student_dashboard, name="student_dashboard"),
#     path('save-grade/', views.enter_grade, name='save_grade'),
#     path('save-attendance/', views.save_attendance, name='save_attendance'),
# ]


# attendance/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('save-attendance/', views.save_attendance, name='save_attendance'),
    path('save-grade/', views.save_grade, name='save_grade'),
    path('student/', views.student_dashboard, name='student_dashboard'),

    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('logout/', views.delete_and_logout, name='logout'),
    path('redirect-user/', views.redirect_user, name='redirect_user'),

    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
]
