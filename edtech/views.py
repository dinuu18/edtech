from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    Booking, Course, EducationBoard, Enrollment, FavoriteTeacher, Grade,
    StudyMaterial, Subject, TeacherProfile, StudentProfile, UserProfile, Wallet,
)


def home(request):
    return render(request, "edtech/home.html", {
        "subjects": Subject.objects.filter(active=True)[:8],
        "teachers": TeacherProfile.objects.filter(verified=True).select_related("user")[:6],
        "courses": Course.objects.filter(active=True).select_related("subject", "teacher", "teacher__user")[:6],
        "stats": {
            "students": UserProfile.objects.filter(role="student").count(),
            "teachers": TeacherProfile.objects.count(),
            "courses": Course.objects.filter(active=True).count(),
            "classes": Booking.objects.filter(status="completed").count(),
        },
    })


def register(request, role):
    if role not in ("student", "teacher"):
        return redirect("home")
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")
        if not all((first_name, username, email, password)):
            messages.error(request, "Please complete all required fields.")
        elif password != confirm:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "That email is already registered.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password,
                                             first_name=first_name, last_name=last_name)
            UserProfile.objects.create(user=user, role=role)
            if role == "teacher":
                profile = TeacherProfile.objects.create(user=user)
                Wallet.objects.create(teacher=profile)
            else:
                StudentProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("dashboard")
    return render(request, "edtech/register.html", {"role": role})


def user_login(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"),
                            password=request.POST.get("password"))
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "edtech/login.html")


@login_required
def user_logout(request):
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    profile = getattr(request.user, "profile", None)
    role = profile.role if profile else "student"
    if role == "teacher":
        teacher = getattr(request.user, "teacher_profile", None)
        if not teacher:
            teacher = TeacherProfile.objects.create(user=request.user)
            Wallet.objects.create(teacher=teacher)
        context = {
            "role": "teacher", "teacher": teacher,
            "courses": teacher.courses.select_related("subject"),
            "bookings": teacher.bookings.select_related("student", "subject").order_by("-starts_at")[:10],
            "earnings": teacher.earnings.aggregate(total=Sum("net_amount"))["total"] or 0,
        }
        return render(request, "edtech/teacher_dashboard.html", context)
    enrollments = Enrollment.objects.filter(student=request.user).select_related("course", "course__subject")
    favorites = FavoriteTeacher.objects.filter(student=request.user).select_related("teacher", "teacher__user")
    context = {
        "role": "student", "enrollments": enrollments, "favorites": favorites,
        "bookings": Booking.objects.filter(student=request.user).select_related("teacher", "teacher__user", "subject").order_by("-starts_at")[:10],
        "materials": StudyMaterial.objects.filter(active=True).select_related("subject")[:8],
    }
    return render(request, "edtech/student_dashboard.html", context)


def subject_list(request):
    subjects = Subject.objects.filter(active=True).prefetch_related("grades").order_by("category", "name")
    return render(request, "edtech/subject_list.html", {"subjects": subjects})


def subject_detail(request, slug):
    subject = get_object_or_404(Subject, slug=slug, active=True)
    return render(request, "edtech/subject_detail.html", {
        "subject": subject,
        "teachers": subject.teachers.filter(available=True).select_related("user"),
        "courses": subject.courses.filter(active=True).select_related("teacher", "teacher__user"),
        "materials": subject.materials.filter(active=True),
    })


def find_tutor(request):
    teachers = TeacherProfile.objects.select_related("user").prefetch_related("subjects", "grades", "boards")
    query = request.GET.get("q", "").strip()
    subject = request.GET.get("subject")
    grade = request.GET.get("grade")
    board = request.GET.get("board")
    language = request.GET.get("language")
    min_fee = request.GET.get("min_fee")
    max_fee = request.GET.get("max_fee")
    experience = request.GET.get("experience")
    rating = request.GET.get("rating")
    if query:
        teachers = teachers.filter(Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) |
                                   Q(user__username__icontains=query) | Q(qualifications__icontains=query))
    if subject:
        teachers = teachers.filter(subjects__id=subject)
    if grade:
        teachers = teachers.filter(grades__id=grade)
    if board:
        teachers = teachers.filter(boards__id=board)
    if language:
        teachers = teachers.filter(languages__icontains=language)
    if min_fee:
        teachers = teachers.filter(hourly_fee__gte=min_fee)
    if max_fee:
        teachers = teachers.filter(hourly_fee__lte=max_fee)
    if experience:
        teachers = teachers.filter(experience_years__gte=experience)
    if request.GET.get("verified"):
        teachers = teachers.filter(verified=True)
    if request.GET.get("available"):
        teachers = teachers.filter(available=True)
    if request.GET.get("online"):
        teachers = teachers.filter(online=True)
    if request.GET.get("offline"):
        teachers = teachers.filter(offline=True)
    if request.GET.get("demo"):
        teachers = teachers.filter(free_demo=True)
    if rating:
        teachers = teachers.annotate(avg_rating=Avg("reviews__rating")).filter(avg_rating__gte=rating)
    sort = request.GET.get("sort")
    if sort == "lowest":
        teachers = teachers.order_by("hourly_fee")
    elif sort == "highest":
        teachers = teachers.order_by("-hourly_fee")
    elif sort == "experienced":
        teachers = teachers.order_by("-experience_years")
    elif sort == "recent":
        teachers = teachers.order_by("-id")
    else:
        teachers = teachers.order_by("-verified", "-id")
    page = Paginator(teachers.distinct(), 9).get_page(request.GET.get("page"))
    return render(request, "edtech/find_tutor.html", {
        "page": page, "subjects": Subject.objects.filter(active=True),
        "grades": Grade.objects.all(), "boards": EducationBoard.objects.all(),
    })


def teacher_detail(request, pk):
    teacher = get_object_or_404(TeacherProfile.objects.select_related("user").prefetch_related("subjects", "grades", "boards"), pk=pk)
    is_favorite = request.user.is_authenticated and FavoriteTeacher.objects.filter(student=request.user, teacher=teacher).exists()
    return render(request, "edtech/teacher_detail.html", {"teacher": teacher, "is_favorite": is_favorite})


def course_detail(request, pk):
    course = get_object_or_404(Course.objects.select_related("subject", "teacher", "teacher__user"), pk=pk)
    is_enrolled = request.user.is_authenticated and Enrollment.objects.filter(student=request.user, course=course).exists()
    return render(request, "edtech/course_detail.html", {"course": course, "is_enrolled": is_enrolled})


@login_required
def enroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    messages.success(request, "You are enrolled successfully." if created else "You are already enrolled.")
    return redirect("course_detail", pk=course.pk)


@login_required
def book_demo(request, pk):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    if request.method == "POST":
        starts_at = request.POST.get("starts_at")
        subject_id = request.POST.get("subject")
        if not starts_at:
            messages.error(request, "Choose a date and time.")
        else:
            try:
                Booking.objects.create(student=request.user, teacher=teacher,
                                       subject=Subject.objects.filter(pk=subject_id).first(),
                                       starts_at=starts_at, is_demo=True, fee=0)
                messages.success(request, "Free demo request submitted.")
                return redirect("dashboard")
            except Exception:
                messages.error(request, "That slot could not be booked. Please choose another.")
    return render(request, "edtech/book_demo.html", {"teacher": teacher, "subjects": teacher.subjects.all()})


@login_required
def favorite_teacher(request, pk):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    favorite = FavoriteTeacher.objects.filter(student=request.user, teacher=teacher)
    if favorite.exists():
        favorite.delete()
        messages.success(request, "Teacher removed from favorites.")
    else:
        FavoriteTeacher.objects.create(student=request.user, teacher=teacher)
        messages.success(request, "Teacher saved.")
    return redirect("teacher_detail", pk=pk)


def material_list(request):
    materials = StudyMaterial.objects.filter(active=True).select_related("subject", "grade")
    subject = request.GET.get("subject")
    query = request.GET.get("q")
    if subject:
        materials = materials.filter(subject_id=subject)
    if query:
        materials = materials.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(request, "edtech/material_list.html", {
        "materials": materials, "subjects": Subject.objects.filter(active=True)
    })


@login_required
def edit_profile(request):
    profile = getattr(request.user, "profile", None)
    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.email = request.POST.get("email", "").strip()
        request.user.save()
        if profile:
            profile.phone = request.POST.get("phone", "").strip()
            profile.save()
        if hasattr(request.user, "teacher_profile"):
            teacher = request.user.teacher_profile
            teacher.headline = request.POST.get("headline", "")
            teacher.biography = request.POST.get("biography", "")
            teacher.qualifications = request.POST.get("qualifications", "")
            teacher.experience_years = int(request.POST.get("experience_years") or 0)
            teacher.hourly_fee = request.POST.get("hourly_fee") or teacher.hourly_fee
            teacher.save()
        messages.success(request, "Profile updated.")
        return redirect("dashboard")
    return render(request, "edtech/edit_profile.html", {"profile": profile})
