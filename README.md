# Tuition.com EdTech Platform

Tuition.com is a Django 4.2 educational marketplace for students and teachers.

## PowerShell setup

```powershell
cd C:\Users\ADMIN\Desktop\dinuworld
python -m pip install django pillow
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Demo accounts use `fiction_student_1` or `fiction_teacher_1` with password `Demo12345!`.

## Included

- Student and teacher registration
- Role-based dashboards
- Advanced tutor search and combined filters
- Subject and course pages
- Course enrollment
- Free demo booking
- Favorite teachers
- Study-material library
- Profile editing
- Django admin management
- Fictional demo data command
- Responsive premium light/dark theme
