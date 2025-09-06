
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Student, Attendance, Grade
from django.contrib.auth import logout
from django.utils.dateparse import parse_date
from django.contrib import messages
from datetime import date
from django.utils import timezone

# Exam types and max marks
EXAM_TYPES = ["Mid1", "Mid2", "Semester"]
EXAM_MAX_MARKS = {
    "Mid1": 30,
    "Mid2": 30,
    "Semester": 100,
}
SUBJECT_LIST = ["CD", "DWDM", "OOAD", "DAA", "IoT"]

ATTENDANCE_START_DATE = date(2025, 9, 1)

# ----------------------------
# Helper: Grade letter
# ----------------------------
def calculate_grade(total, maximum):
    if maximum == 0:
        return "N/A"
    percentage = (total / maximum) * 100
    if percentage >= 90:
        return "S"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    elif percentage >= 35:
        return "E"
    else:
        return "F"

# ----------------------------
# Logout & Redirect
# ----------------------------
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def redirect_user(request):
    return redirect('teacher_dashboard' if request.user.is_staff else 'student_dashboard')

@login_required
def delete_and_logout(request):
    user = request.user
    logout(request)
    user.delete()
    return redirect('login')


@login_required
def student_dashboard(request):
    if request.user.is_staff:
        return redirect('teacher_dashboard')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('login')

    today = timezone.now().date()

    # Attendance
    total_days_since_start = max((today - ATTENDANCE_START_DATE).days + 1, 0)
    latest_attendance = Attendance.objects.filter(student=student).order_by('-date').first()
    attendance_status = latest_attendance.status if latest_attendance else "N/A"
    present_count = Attendance.objects.filter(student=student, status='Present').count()
    absent_count = Attendance.objects.filter(student=student, status='Absent').count()

    # Grades split by exam type
    mid1_grades = Grade.objects.filter(student=student, exam_type__iexact='Mid1')
    mid2_grades = Grade.objects.filter(student=student, exam_type__iexact='Mid2')
    sem_grades = Grade.objects.filter(student=student, exam_type__iexact='Semester')

    # Totals
    mid1_total_grade = sum(g.marks for g in mid1_grades)
    mid2_total_grade = sum(g.marks for g in mid2_grades)
    sem_total_grade = sum(g.marks for g in sem_grades)

    # Max marks
    mid1_max = len(mid1_grades) * EXAM_MAX_MARKS['Mid1'] if mid1_grades.exists() else 30
    mid2_max = len(mid2_grades) * EXAM_MAX_MARKS['Mid2'] if mid2_grades.exists() else 30
    sem_max = len(sem_grades) * EXAM_MAX_MARKS['Semester'] if sem_grades.exists() else 100

    # ✅ Fail rule: if any subject < 40% of max marks → overall grade = F
    def calculate_exam_grade(grades, exam_type, total, max_marks):
        if not grades.exists():
            return "N/A"
        has_fail = any(g.marks < (0.4 * EXAM_MAX_MARKS[exam_type]) for g in grades)
        if has_fail:
            return "F"
        return calculate_grade(total, max_marks)

    mid1_grade_letter = calculate_exam_grade(mid1_grades, 'Mid1', mid1_total_grade, mid1_max)
    mid2_grade_letter = calculate_exam_grade(mid2_grades, 'Mid2', mid2_total_grade, mid2_max)
    sem_grade_letter = calculate_exam_grade(sem_grades, 'Semester', sem_total_grade, sem_max)

    context = {
        'student': student,
        'attendance_status': attendance_status,
        'total_days': total_days_since_start,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_start_date': ATTENDANCE_START_DATE,

        'mid1_grades': mid1_grades,
        'mid2_grades': mid2_grades,
        'sem_grades': sem_grades,

        'mid1_total_grade': mid1_total_grade,
        'mid2_total_grade': mid2_total_grade,
        'sem_total_grade': sem_total_grade,

        'mid1_max': mid1_max,
        'mid2_max': mid2_max,
        'sem_max': sem_max,

        'mid1_grade_letter': mid1_grade_letter,
        'mid2_grade_letter': mid2_grade_letter,
        'sem_grade_letter': sem_grade_letter,
    }

    return render(request, 'attendance/student_dashboard.html', context)



# ----------------------------
# Teacher Dashboard
# ----------------------------

@login_required
def teacher_dashboard(request):
    if not request.user.is_staff:
        return redirect('student_dashboard')

    students = Student.objects.select_related('user').all().order_by('roll_number')
    today = timezone.now().date()
    total_days_since_start = max((today - ATTENDANCE_START_DATE).days, 0)

    # Attendance mapping
    latest_att_map = {att.student_id: att.status for att in Attendance.objects.filter(date=today)}

    # Next student for attendance
    next_student_attendance = None
    for student in students:
        if not Attendance.objects.filter(student=student, date=today).exists():
            next_student_attendance = student
            break

    # Selected exam type
    selected_exam_type = request.GET.get('exam_type', EXAM_TYPES[0])

    # Total grades for each student (selected exam type)
    total_grade_map = {}
    for student in students:
        grades = Grade.objects.filter(student=student, exam_type__iexact=selected_exam_type)
        if grades.exists():
            # ✅ check fail per subject
            has_fail = any(g.marks < (0.4 * EXAM_MAX_MARKS[selected_exam_type]) for g in grades)  
            if has_fail:
                total_grade_map[student.id] = "F"
            else:
                max_marks = len(grades) * EXAM_MAX_MARKS[selected_exam_type]
                total = sum(g.marks for g in grades)
                total_grade_map[student.id] = calculate_grade(total, max_marks)
        else:
            total_grade_map[student.id] = "N/A"

    # Attach attendance & grades
    for s in students:
        s.attendance_status = latest_att_map.get(s.id, "N/A")
        s.grade_value = total_grade_map.get(s.id, "N/A")
        s.present_count = Attendance.objects.filter(student=s, status='Present').count()
        s.absent_count = Attendance.objects.filter(student=s, status='Absent').count()
        s.total_days = total_days_since_start

        # Grades per exam type
        def calculate_exam_grade(exam_type):
            grades = Grade.objects.filter(student=s, exam_type__iexact=exam_type)
            if not grades.exists():
                return "N/A"

            # ✅ fail rule: 40% of max marks per subject
            has_fail = any(g.marks < (0.4 * EXAM_MAX_MARKS[exam_type]) for g in grades)
            if has_fail:
                return "F"

            total = sum(g.marks for g in grades)
            max_marks = len(grades) * EXAM_MAX_MARKS[exam_type]
            return calculate_grade(total, max_marks)

        s.mid1_grade = calculate_exam_grade('Mid1')
        s.mid2_grade = calculate_exam_grade('Mid2')
        s.sem_grade = calculate_exam_grade('Semester')

    # Next student + subject for grading
    next_student_grade = None
    next_subject = None
    for student in students:
        ungraded_subjects = [
            subject for subject in SUBJECT_LIST
            if not Grade.objects.filter(student=student, subject=subject, exam_type__iexact=selected_exam_type).exists()
        ]
        if ungraded_subjects:
            next_student_grade = student
            next_subject = ungraded_subjects[0]
            break

    context = {
        'students': students,
        'subjects': SUBJECT_LIST,
        'exam_types': EXAM_TYPES,
        'next_student_grade': next_student_grade,
        'next_subject': next_subject,
        'next_student_attendance': next_student_attendance,
        'selected_exam_type': selected_exam_type,
        'today': today,
    }

    return render(request, 'attendance/teacher_dashboard.html', context)



# ----------------------------
# Save Grade
# ----------------------------
@login_required
def save_grade(request):
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        subject = request.POST.get('subject')
        marks = request.POST.get('marks')
        exam_type = request.POST.get('exam_type')

        # Validate marks
        try:
            marks = int(marks)
        except (ValueError, TypeError):
            messages.error(request, "Invalid marks value.")
            return redirect(f'/teacher/?exam_type={exam_type}')

        # Validate student
        try:
            student = Student.objects.get(roll_number=roll_number)
        except Student.DoesNotExist:
            messages.error(request, "Student not found.")
            return redirect(f'/teacher/?exam_type={exam_type}')

        # Prevent duplicate
        if Grade.objects.filter(student=student, subject=subject, exam_type__iexact=exam_type).exists():
            messages.error(request, f"{exam_type} marks for {subject} already entered.")
            return redirect(f'/teacher/?exam_type={exam_type}')

        Grade.objects.create(student=student, subject=subject, marks=marks, exam_type=exam_type)
        messages.success(request, f"{exam_type} marks saved for {student.roll_number} in {subject}.")
        return redirect(f'/teacher/?exam_type={exam_type}')

# ----------------------------
# Save Attendance
# ----------------------------
@login_required
def save_attendance(request):
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number', '').strip()
        attendance_status = request.POST.get('attendance')
        date_str = request.POST.get('date', '')

        if not roll_number or not attendance_status:
            messages.error(request, "Roll number and attendance are required.")
            return redirect('teacher_dashboard')

        try:
            student = Student.objects.get(roll_number=roll_number)
        except Student.DoesNotExist:
            messages.error(request, f"Student with roll {roll_number} not found.")
            return redirect('teacher_dashboard')

        dt = parse_date(date_str) if date_str else date.today()

        if Attendance.objects.filter(student=student, date=dt).exists():
            messages.warning(request, f"Attendance already marked for {student.roll_number} on {dt}.")
        else:
            Attendance.objects.create(student=student, date=dt, status=attendance_status)
            messages.success(request, f"Attendance saved for {student.user.get_full_name() or student.user.username}.")

    return redirect('teacher_dashboard')
