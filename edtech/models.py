from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class Grade(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class EducationBoard(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    CATEGORY_CHOICES = [
        ("School", "School Education"), ("Commerce", "Commerce"),
        ("Technology", "Technology"), ("Competitive", "Competitive Exams"),
    ]
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default="book-open")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    grades = models.ManyToManyField(Grade, blank=True)
    boards = models.ManyToManyField(EducationBoard, blank=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [("student", "Student"), ("teacher", "Teacher"), ("admin", "Admin")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    board = models.ForeignKey(EducationBoard, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_subjects = models.ManyToManyField(Subject, blank=True, related_name="interested_students")


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    headline = models.CharField(max_length=180, blank=True)
    biography = models.TextField(blank=True)
    qualifications = models.CharField(max_length=250, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    subjects = models.ManyToManyField(Subject, related_name="teachers", blank=True)
    grades = models.ManyToManyField(Grade, blank=True)
    boards = models.ManyToManyField(EducationBoard, blank=True)
    languages = models.CharField(max_length=150, blank=True)
    hourly_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500)
    online = models.BooleanField(default=True)
    offline = models.BooleanField(default=False)
    free_demo = models.BooleanField(default=True)
    introduction_video = models.URLField(blank=True)
    verified = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    completed_classes = models.PositiveIntegerField(default=0)

    @property
    def rating(self):
        return self.reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0

    @property
    def review_count(self):
        return self.reviews.count()

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    learning_goals = models.TextField(blank=True)


class Course(models.Model):
    LEVEL_CHOICES = [("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced")]
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="courses")
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    board = models.ForeignKey(EducationBoard, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="courses")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="Beginner")
    language = models.CharField(max_length=50, default="English")
    outcomes = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=180)
    video_url = models.URLField(blank=True)
    content = models.TextField(blank=True)
    duration = models.CharField(max_length=30, blank=True)
    order = models.PositiveIntegerField(default=1)


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    progress = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")


class TeacherAvailability(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="availability")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()


class Booking(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("confirmed", "Confirmed"), ("completed", "Completed"), ("cancelled", "Cancelled"), ("rejected", "Rejected")]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="bookings")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    starts_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    is_demo = models.BooleanField(default=False)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["teacher", "starts_at"], name="unique_teacher_booking_slot")
        ]


class StudyMaterial(models.Model):
    title = models.CharField(max_length=180)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="materials")
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to="study_materials/", blank=True)
    external_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="reviews")
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("teacher", "student")


class FavoriteTeacher(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_teachers")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ("student", "teacher")


class Quiz(models.Model):
    title = models.CharField(max_length=180)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="quizzes")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="quizzes")
    duration_minutes = models.PositiveIntegerField(default=30)
    active = models.BooleanField(default=True)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    option_a = models.CharField(max_length=250)
    option_b = models.CharField(max_length=250)
    option_c = models.CharField(max_length=250)
    option_d = models.CharField(max_length=250)
    correct_option = models.CharField(max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    explanation = models.TextField(blank=True)


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Wallet(models.Model):
    teacher = models.OneToOneField(TeacherProfile, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class TeacherEarning(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="earnings")
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="earning")
    gross_amount = models.DecimalField(max_digits=8, decimal_places=2)
    commission = models.DecimalField(max_digits=8, decimal_places=2)
    net_amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=150)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
