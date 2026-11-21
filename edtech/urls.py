from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/<str:role>/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/<slug:slug>/", views.subject_detail, name="subject_detail"),
    path("tutors/", views.find_tutor, name="find_tutor"),
    path("teachers/<int:pk>/", views.teacher_detail, name="teacher_detail"),
    path("courses/<int:pk>/", views.course_detail, name="course_detail"),
    path("courses/<int:pk>/enroll/", views.enroll_course, name="enroll_course"),
    path("teachers/<int:pk>/book/", views.book_demo, name="book_demo"),
    path("teachers/<int:pk>/favorite/", views.favorite_teacher, name="favorite_teacher"),
    path("materials/", views.material_list, name="material_list"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
]
