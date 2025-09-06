# from django.contrib.auth.decorators import login_required
# from django.shortcuts import redirect, render
# from .models import Student, Attendance, Grade
# from django.contrib.auth import logout
# from django.utils.dateparse import parse_date
# from django.contrib import messages
# from datetime import date

# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.utils import timezone
# from django.contrib import messages

# from .models import Student, Attendance, Grade

# EXAM_TYPES = {
#     "Mid1": 30,
#     "Mid2": 30,
#     "Semester": 100,
# }
# SUBJECT_LIST = ["CD", "DWDM", "OOAD", "DAA", "IoT"]

# def logout_view(request):
#     logout(request)
#     messages.success(request, "You have been logged out successfully.")
#     return redirect('login')

# @login_required
# def redirect_user(request):
#     if request.user.is_staff:
#         return redirect('teacher_dashboard')
#     else:
#         return redirect('student_dashboard')

# @login_required
# def delete_and_logout(request):
#     user = request.user
#     logout(request)   # End the session first
#     user.delete()     # Remove user account from DB
#     return redirect('login')  # Redirect to login page after deletion

# # ----------------------------
# # Helper: Grade letter based on percentage
# # ----------------------------
# def calculate_grade(total, maximum):
#     if maximum == 0:
#         return "N/A"
#     percentage = (total / maximum) * 100
#     if percentage >= 90:
#         return "S"
#     elif percentage >= 80:
#         return "A"
#     elif percentage >= 70:
#         return "B"
#     elif percentage >= 60:
#         return "C"
#     elif percentage >= 50:
#         return "D"
#     elif percentage >= 35:
#         return "E"
#     else:
#         return "F"

# ATTENDANCE_START_DATE = date(2025, 9, 1)
# # ----------------------------
# # Student Dashboard
# # ----------------------------
# @login_required
# def student_dashboard(request):
#     if request.user.is_staff:
#         return redirect('teacher_dashboard')

#     try:
#         student = Student.objects.get(user=request.user)
#     except Student.DoesNotExist:
#         return redirect('login')

#     today = timezone.now().date()

#     # Attendance
#     total_days_since_start = (today - ATTENDANCE_START_DATE).days + 1
#     if total_days_since_start < 0:
#         total_days_since_start = 0

#     latest_attendance = Attendance.objects.filter(student=student).order_by('-date').first()
#     attendance_status = latest_attendance.status if latest_attendance else "N/A"

#     present_count = Attendance.objects.filter(student=student, status='Present').count()
#     absent_count = Attendance.objects.filter(student=student, status='Absent').count()

#     # Grades split by exam type
#     mid1_grades = Grade.objects.filter(student=student, exam_type__iexact='mid1')
#     mid2_grades = Grade.objects.filter(student=student, exam_type__iexact='mid2')
#     sem_grades = Grade.objects.filter(student=student, exam_type__iexact='semester')

#     # Totals
#     mid1_total = sum(g.marks for g in mid1_grades)
#     mid2_total = sum(g.marks for g in mid2_grades)
#     sem_total = sum(g.marks for g in sem_grades)

#     # Max marks for each exam type
#     mid1_max = len(mid1_grades) * 30
#     mid2_max = len(mid2_grades) * 30
#     sem_max = len(sem_grades) * 100

#     # Grade letters
#     mid1_grade = calculate_grade(mid1_total, mid1_max)
#     mid2_grade = calculate_grade(mid2_total, mid2_max)
#     sem_grade = calculate_grade(sem_total, sem_max)

#     context = {
#         'student': student,
#         'attendance_status': attendance_status,
#         'total_days': total_days_since_start,
#         'present_count': present_count,
#         'absent_count': absent_count,

#         'mid1_grades': mid1_grades,
#         'mid2_grades': mid2_grades,
#         'sem_grades': sem_grades,

#         'mid1_total_grade': mid1_total,
#         'mid2_total_grade': mid2_total,
#         'sem_total_grade': sem_total,

#         'mid1_grade_letter': mid1_grade,
#         'mid2_grade_letter': mid2_grade,
#         'sem_grade_letter': sem_grade,
#     }
#     return render(request, 'attendance/student_dashboard.html', context)


# # ----------------------------
# # Teacher Dashboard
# # ----------------------------
# @login_required
# def teacher_dashboard(request):
#     if not request.user.is_staff:
#         return redirect('student_dashboard')

#     students = list(Student.objects.select_related('user').all().order_by('roll_number'))
#     today = timezone.now().date()
#     total_days_since_start = max((today - ATTENDANCE_START_DATE).days, 0)

#     # Today's attendance
#     latest_att_map = {att.student_id: att.status for att in Attendance.objects.filter(date=today)}

#     # Next student for attendance
#     next_student_attendance = None
#     for student in students:
#         if not Attendance.objects.filter(student=student, date=today).exists():
#             next_student_attendance = student
#             break

#     # Selected exam type
#     selected_exam_type = request.GET.get('exam_type', EXAM_TYPES[0])  # default to first

#     # Grade calculation
#     total_grade_map = {}
#     for student in students:
#         grades = Grade.objects.filter(student=student, exam_type=selected_exam_type)
#         if not grades.exists():
#             total_grade_map[student.id] = "N/A"
#             continue

#         # Dynamic max marks based on exam type
#         if selected_exam_type.lower() in ['mid1', 'mid2']:
#             max_marks = len(grades) * 30
#         elif selected_exam_type.lower() == 'semester':
#             max_marks = len(grades) * 100
#         else:
#             max_marks = len(grades) * 100  # fallback

#         total = sum(g.marks for g in grades)
#         grade_letter = calculate_grade(total, max_marks)
#         total_grade_map[student.id] = grade_letter

#     # Attach data to each student
#     for s in students:
#         s.attendance_status = latest_att_map.get(s.id, "N/A")
#         s.grade_value = total_grade_map.get(s.id, "N/A")
#         s.present_count = Attendance.objects.filter(student=s, status='Present').count()
#         s.absent_count = Attendance.objects.filter(student=s, status='Absent').count()
#         s.total_days = total_days_since_start

#     # Next student + subject for grading
#     next_student_grade = None
#     next_subject = None
#     for student in students:
#         ungraded_subjects = [
#             subject for subject in SUBJECT_LIST
#             if not Grade.objects.filter(student=student, subject=subject, exam_type=selected_exam_type).exists()
#         ]
#         if ungraded_subjects:
#             next_student_grade = student
#             next_subject = ungraded_subjects[0]
#             break

#     return render(request, 'attendance/teacher_dashboard.html', {
#         'students': students,
#         'subjects': SUBJECT_LIST,
#         'exam_types': EXAM_TYPES,
#         'next_student_grade': next_student_grade,
#         'next_subject': next_subject,
#         'next_student_attendance': next_student_attendance,
#         'selected_exam_type': selected_exam_type,
#         'today': today
#     })


# # ----------------------------
# # Save Grade
# # ----------------------------
# @login_required
# def save_grade(request):
#     if request.method == 'POST':
#         roll_number = request.POST.get('roll_number')
#         subject = request.POST.get('subject')
#         marks = request.POST.get('marks')
#         exam_type = request.POST.get('exam_type')

#         # Validate marks input
#         try:
#             marks = int(marks)
#         except (ValueError, TypeError):
#             messages.error(request, "Invalid marks value.")
#             return redirect(f'/teacher/?exam_type={exam_type}')

#         # Validate student
#         try:
#             student = Student.objects.get(roll_number=roll_number)
#         except Student.DoesNotExist:
#             messages.error(request, "Student not found.")
#             return redirect(f'/teacher/?exam_type={exam_type}')

#         # Prevent duplicate entry
#         if Grade.objects.filter(student=student, subject=subject, exam_type=exam_type).exists():
#             messages.error(
#                 request,
#                 f"{exam_type} marks for {subject} already entered for roll number {student.roll_number}."
#             )
#             return redirect(f'/teacher/?exam_type={exam_type}')

#         # Save grade
#         Grade.objects.create(student=student, subject=subject, marks=marks, exam_type=exam_type)
#         messages.success(
#             request,
#             f"{exam_type} marks saved for roll number {student.roll_number} in {subject}."
#         )
#         return redirect(f'/teacher/?exam_type={exam_type}')



# @login_required
# def save_attendance(request):
#     """
#     Save attendance for the 'next student' in order.
#     Prevents duplicates for today.
#     """
#     if request.method == 'POST':
#         roll_number = request.POST.get('roll_number', '').strip()
#         attendance_status = request.POST.get('attendance')
#         date_str = request.POST.get('date', '')  # optional; default = today

#         if not roll_number or not attendance_status:
#             messages.error(request, "Roll number and attendance are required.")
#             return redirect('teacher_dashboard')

#         try:
#             student = Student.objects.get(roll_number=roll_number)
#         except Student.DoesNotExist:
#             messages.error(request, f"Student with roll {roll_number} not found.")
#             return redirect('teacher_dashboard')

#         # Parse date or use today
#         if date_str:
#             try:
#                 dt = parse_date(date_str)
#             except:
#                 dt = date.today()
#         else:
#             dt = date.today()

#         # Prevent duplicate entries for same day
#         if Attendance.objects.filter(student=student, date=dt).exists():
#             messages.warning(request, f"Attendance already marked for {student.roll_number} on {dt}.")
#         else:
#             Attendance.objects.create(student=student, date=dt, status=attendance_status)
#             messages.success(request, f"Attendance saved for {student.user.get_full_name() or student.user.username}.")

#     return redirect('teacher_dashboard')


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

# ----------------------------
# Student Dashboard
# ----------------------------
# @login_required
# def student_dashboard(request):
#     if request.user.is_staff:
#         return redirect('teacher_dashboard')

#     try:
#         student = Student.objects.get(user=request.user)
#     except Student.DoesNotExist:
#         return redirect('login')

#     today = timezone.now().date()

#     # Attendance
#     total_days_since_start = max((today - ATTENDANCE_START_DATE).days + 1, 0)
#     latest_attendance = Attendance.objects.filter(student=student).order_by('-date').first()
#     attendance_status = latest_attendance.status if latest_attendance else "N/A"
#     present_count = Attendance.objects.filter(student=student, status='Present').count()
#     absent_count = Attendance.objects.filter(student=student, status='Absent').count()

#     # Grades by exam type
#     grades_by_type = {}
#     for exam in EXAM_TYPES:
#         grades = Grade.objects.filter(student=student, exam_type__iexact=exam)
#         total = sum(g.marks for g in grades)
#         max_marks = sum(EXAM_MAX_MARKS[exam] for _ in grades)
#         grade_letter = calculate_grade(total, max_marks)
#         grades_by_type[exam] = {
#             'grades': grades,
#             'total': total,
#             'max': max_marks,
#             'letter': grade_letter
#         }

#     context = {
#         'student': student,
#         'attendance_status': attendance_status,
#         'total_days': total_days_since_start,
#         'present_count': present_count,
#         'absent_count': absent_count,
#         'grades_by_type': grades_by_type,
#     }
#     return render(request, 'attendance/student_dashboard.html', context)


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
    mid1_max = len(mid1_grades) * EXAM_MAX_MARKS['Mid1'] if mid1_grades else 30
    mid2_max = len(mid2_grades) * EXAM_MAX_MARKS['Mid2'] if mid2_grades else 30
    sem_max = len(sem_grades) * EXAM_MAX_MARKS['Semester'] if sem_grades else 100

    # Grade letters
    mid1_grade_letter = calculate_grade(mid1_total_grade, mid1_max)
    mid2_grade_letter = calculate_grade(mid2_total_grade, mid2_max)
    sem_grade_letter = calculate_grade(sem_total_grade, sem_max)

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

    # Total grades for each student
    total_grade_map = {}
    for student in students:
        grades = Grade.objects.filter(student=student, exam_type__iexact=selected_exam_type)
        if grades.exists():
            max_marks = sum(EXAM_MAX_MARKS[selected_exam_type] for _ in grades)
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
        mid1 = Grade.objects.filter(student=s, exam_type__iexact='Mid1')
        mid2 = Grade.objects.filter(student=s, exam_type__iexact='Mid2')
        sem = Grade.objects.filter(student=s, exam_type__iexact='Semester')

        s.mid1_grade = calculate_grade(sum(g.marks for g in mid1), EXAM_MAX_MARKS['Mid1']) if mid1.exists() else "N/A"
        s.mid2_grade = calculate_grade(sum(g.marks for g in mid2), EXAM_MAX_MARKS['Mid2']) if mid2.exists() else "N/A"
        s.sem_grade = calculate_grade(sum(g.marks for g in sem), EXAM_MAX_MARKS['Semester']) if sem.exists() else "N/A"

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

# def teacher_dashboard(request):
#     students = Student.objects.all()

#     # Calculate total days since attendance start
#     ATTENDANCE_START_DATE = date.today()  # or your start date
#     total_days_since_start = (date.today() - ATTENDANCE_START_DATE).days + 1

#     for student in students:
#         # Fetch grades per exam type
#         mid1_grades = Grade.objects.filter(student=student, exam_type__iexact='Mid1')
#         mid2_grades = Grade.objects.filter(student=student, exam_type__iexact='Mid2')
#         sem_grades = Grade.objects.filter(student=student, exam_type__iexact='Semester')

#         # Calculate total marks per exam
#         mid1_total = sum(g.marks for g in mid1_grades)
#         mid2_total = sum(g.marks for g in mid2_grades)
#         sem_total = sum(g.marks for g in sem_grades)

#         # Max marks per exam
#         mid1_max = EXAM_MAX_MARKS['Mid1']
#         mid2_max = EXAM_MAX_MARKS['Mid2']
#         sem_max = EXAM_MAX_MARKS['Semester']

#         # Assign grades to student object
#         student.mid1_grade = calculate_grade(mid1_total, mid1_max) if mid1_grades else "N/A"
#         student.mid2_grade = calculate_grade(mid2_total, mid2_max) if mid2_grades else "N/A"
#         student.sem_grade = calculate_grade(sem_total, sem_max) if sem_grades else "N/A"

#         # Attendance counts
#         student.present_count = Attendance.objects.filter(student=student, status='Present').count()
#         student.absent_count = Attendance.objects.filter(student=student, status='Absent').count()
#         student.total_days = total_days_since_start

#     context = {
#         'students': students
#     }
#     return render(request, 'attendance/teacher_dashboard.html', context)

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
