from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Student, Attendance, Grade
from django.contrib.auth import logout
from django.utils.dateparse import parse_date
from django.contrib import messages
from datetime import date

@login_required
def teacher_dashboard(request):
    if not request.user.is_staff:
        return redirect('student_dashboard')

    # Fetch students
    students = list(Student.objects.select_related('user').all().order_by('roll_number'))

    # Build quick lookup for latest attendance
    latest_att_map = {}
    for att in Attendance.objects.order_by('-date'):
        sid = att.student_id
        if sid not in latest_att_map:
            latest_att_map[sid] = att.status

    # Calculate total grade for each student
    total_grade_map = {}
    for student in students:
        grades = Grade.objects.filter(student=student)

        if not grades.exists():
            total_grade_map[student.id] = "N/A"
            continue

        marks_list = [g.marks for g in grades]

        # Fail if any subject < 35
        if any(m < 35 for m in marks_list):
            grade_letter = "F"
        else:
            avg_marks = sum(marks_list) / len(marks_list)
            if avg_marks >= 90:
                grade_letter = "S"
            elif avg_marks >= 80:
                grade_letter = "A"
            elif avg_marks >= 70:
                grade_letter = "B"
            elif avg_marks >= 60:
                grade_letter = "C"
            elif avg_marks >= 50:
                grade_letter = "D"
            elif avg_marks >= 35:
                grade_letter = "E"
            else:
                grade_letter = "F"

        total_grade_map[student.id] = grade_letter

    # Attach data to student objects
    for s in students:
        s.attendance_status = latest_att_map.get(s.id, "N/A")
        s.grade_value = total_grade_map.get(s.id, "N/A")

    return render(request, 'attendance/teacher_dashboard.html', {'students': students})


@login_required
def save_attendance(request):
    """
    Handles form POST:
    - expects 'roll_number' and 'attendance' and optional 'date'
    """
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number', '').strip()
        attendance_status = request.POST.get('attendance')
        date_str = request.POST.get('date', '')  # optional; if empty use today

        if not roll_number or not attendance_status:
            messages.error(request, "Roll number and attendance are required.")
            return redirect('teacher_dashboard')

        try:
            student = Student.objects.get(roll_number=roll_number)
        except Student.DoesNotExist:
            messages.error(request, f"Student with roll {roll_number} not found.")
            return redirect('teacher_dashboard')

        # parse date or use today
        if date_str:
            try:
                dt = parse_date(date_str)
            except:
                dt = date.today()
        else:
            dt = date.today()

        Attendance.objects.update_or_create(
            student=student,
            date=dt,
            defaults={'status': attendance_status}
        )
        messages.success(request, f"Attendance saved for {student.user.get_full_name() or student.user.username}.")
    return redirect('teacher_dashboard')

# @login_required
# def save_grade(request):
#     """
#     Handles form POST:
#     - expects 'roll_number', 'subject' (optional) and 'marks'
#     """
#     if request.method == 'POST':
#         roll_number = request.POST.get('roll_number', '').strip()
#         subject = request.POST.get('subject', 'General').strip()
#         marks = request.POST.get('marks', '').strip()

#         if not roll_number or marks == '':
#             messages.error(request, "Roll number and marks are required.")
#             return redirect('teacher_dashboard')

#         try:
#             student = Student.objects.get(roll_number=roll_number)
#         except Student.DoesNotExist:
#             messages.error(request, f"Student with roll {roll_number} not found.")
#             return redirect('teacher_dashboard')

#         try:
#             marks_int = int(marks)
#         except ValueError:
#             messages.error(request, "Marks must be an integer.")
#             return redirect('teacher_dashboard')

#         Grade.objects.create(student=student, subject=subject, marks=marks_int)
#         messages.success(request, f"Grade ({marks_int}) saved for {student.user.get_full_name() or student.user.username}.")

#     return redirect('teacher_dashboard')


@login_required
def save_grade(request):
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        subject = request.POST.get('subject')
        marks = request.POST.get('marks')

        # Validate marks input
        try:
            marks = int(marks)
        except ValueError:
            messages.error(request, "Invalid marks value.")
            return redirect('teacher_dashboard')

        # Find student
        try:
            student = Student.objects.get(roll_number=roll_number)
        except Student.DoesNotExist:
            messages.error(request, "Student not found.")
            return redirect('teacher_dashboard')

        # Check for duplicate subject entry
        if Grade.objects.filter(student=student, subject=subject).exists():
            messages.error(request, f"Grade for {subject} already exists for {student.roll_number}.")
            return redirect('teacher_dashboard')

        # Save grade
        Grade.objects.create(student=student, subject=subject, marks=marks)
        messages.success(request, f"Grade saved for {student.roll_number} in {subject}.")
        return redirect('teacher_dashboard')

    return redirect('teacher_dashboard')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Student, Attendance, Grade

@login_required
def student_dashboard(request):
    # Ensure the logged-in user is a student, not a teacher
    if request.user.is_staff:
        return redirect('teacher_dashboard')

    # Get the Student object for the logged-in user
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('login')

    # Latest attendance
    latest_attendance = Attendance.objects.filter(student=student).order_by('-date').first()
    attendance_status = latest_attendance.status if latest_attendance else "N/A"

    # Get all grades for the student
    grades = Grade.objects.filter(student=student)

    # Calculate grade value
    if grades.exists():
        subject_marks = {g.subject: g.marks for g in grades}

        # Fail if any subject < 40
        if any(m < 40 for m in subject_marks.values()):
            total_grade = "F"
        else:
            total_marks = sum(subject_marks.values())
            average = total_marks / len(subject_marks)

            if average >= 90:
                total_grade = "A"
            elif average >= 80:
                total_grade = "B"
            elif average >= 70:
                total_grade = "C"
            elif average >= 60:
                total_grade = "D"
            else:
                total_grade = "F"
    else:
        total_grade = "N/A"

    context = {
        'student': student,
        'attendance_status': attendance_status,
        'grades': grades,
        'total_grade': total_grade,
    }
    return render(request, 'attendance/student_dashboard.html', context)


@login_required
def redirect_user(request):
    if request.user.is_staff:
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')

@login_required
def delete_and_logout(request):
    user = request.user
    logout(request)   # End the session first
    user.delete()     # Remove user account from DB
    return redirect('login')  # Redirect to login page after deletion