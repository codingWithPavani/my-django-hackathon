from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Student, Attendance, Grade
from django.contrib.auth import logout
from django.utils.dateparse import parse_date
from django.contrib import messages
from datetime import date



def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


# Set attendance start date
ATTENDANCE_START_DATE = date(2025, 9, 1)

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

    today = timezone.now().date()

    # Calculate total days from ATTENDANCE_START_DATE
    total_days_since_start = (today - ATTENDANCE_START_DATE).days + 1
    if total_days_since_start < 0:
        total_days_since_start = 0

    # Latest attendance
    latest_attendance = Attendance.objects.filter(student=student).order_by('-date').first()
    attendance_status = latest_attendance.status if latest_attendance else "N/A"

    # Count Present and Absent days
    present_count = Attendance.objects.filter(student=student, status='Present').count()
    absent_count = Attendance.objects.filter(student=student, status='Absent').count()

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
        'total_days': total_days_since_start,
        'present_count': present_count,
        'absent_count': absent_count,
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



@login_required
def save_attendance(request):
    """
    Save attendance for the 'next student' in order.
    Prevents duplicates for today.
    """
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number', '').strip()
        attendance_status = request.POST.get('attendance')
        date_str = request.POST.get('date', '')  # optional; default = today

        if not roll_number or not attendance_status:
            messages.error(request, "Roll number and attendance are required.")
            return redirect('teacher_dashboard')

        try:
            student = Student.objects.get(roll_number=roll_number)
        except Student.DoesNotExist:
            messages.error(request, f"Student with roll {roll_number} not found.")
            return redirect('teacher_dashboard')

        # Parse date or use today
        if date_str:
            try:
                dt = parse_date(date_str)
            except:
                dt = date.today()
        else:
            dt = date.today()

        # Prevent duplicate entries for same day
        if Attendance.objects.filter(student=student, date=dt).exists():
            messages.warning(request, f"Attendance already marked for {student.roll_number} on {dt}.")
        else:
            Attendance.objects.create(student=student, date=dt, status=attendance_status)
            messages.success(request, f"Attendance saved for {student.user.get_full_name() or student.user.username}.")

    return redirect('teacher_dashboard')



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from .models import Student, Attendance, Grade

ATTENDANCE_START_DATE = date(2025, 9, 1)

# Define subjects in order
SUBJECT_LIST = ['CD', 'DWDM', 'OOAD', 'DAA', 'IoT']


@login_required
def teacher_dashboard(request):
    if not request.user.is_staff:
        return redirect('student_dashboard')

    students = list(Student.objects.select_related('user').all().order_by('roll_number'))
    today = timezone.now().date()
    total_days_since_start = max((today - ATTENDANCE_START_DATE).days, 0)

    # Get attendance status
    attended_ids = Attendance.objects.filter(date=today).values_list('student_id', flat=True)
    next_student = None
    for s in students:
        if s.id not in attended_ids:
            next_student = s
            break

    # Latest attendance map
    latest_att_map = {att.student_id: att.status for att in Attendance.objects.order_by('-date')}

    # Total grade map
    total_grade_map = {}
    for student in students:
        grades = Grade.objects.filter(student=student)
        if not grades.exists():
            total_grade_map[student.id] = "N/A"
            continue
        marks_list = [g.marks for g in grades]
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

    # Attach attributes
    for s in students:
        s.attendance_status = latest_att_map.get(s.id, "N/A")
        s.grade_value = total_grade_map.get(s.id, "N/A")
        s.present_count = Attendance.objects.filter(student=s, status='Present').count()
        s.absent_count = Attendance.objects.filter(student=s, status='Absent').count()
        s.total_days = total_days_since_start

    # Determine next subject for current student
    next_subject = None
    if 'current_student_roll' not in request.session:
        request.session['current_student_roll'] = students[0].roll_number if students else None
        request.session['subject_index'] = 0

    if request.session.get('current_student_roll'):
        try:
            current_student = Student.objects.get(roll_number=request.session['current_student_roll'])
            submitted_subjects = Grade.objects.filter(student=current_student).values_list('subject', flat=True)
            for i, subj in enumerate(SUBJECT_LIST):
                if subj not in submitted_subjects:
                    next_subject = subj
                    request.session['subject_index'] = i
                    break
            else:
                # All subjects done, move to next student
                next_student_index = students.index(current_student) + 1
                if next_student_index < len(students):
                    next_student_roll = students[next_student_index].roll_number
                    request.session['current_student_roll'] = next_student_roll
                    request.session['subject_index'] = 0
                    next_subject = SUBJECT_LIST[0]
                else:
                    request.session['current_student_roll'] = None
                    next_subject = None
        except Student.DoesNotExist:
            request.session['current_student_roll'] = None
            next_subject = None

    return render(request, 'attendance/teacher_dashboard.html', {
        'students': students,
        'next_student': next_student,
        'current_student_roll': request.session.get('current_student_roll'),
        'next_subject': next_subject,
    })


@login_required
def save_grade(request):
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        subject = request.POST.get('subject')
        marks = request.POST.get('marks')

        # Validate marks
        try:
            marks = int(marks)
        except ValueError:
            messages.error(request, "Invalid marks value.")
            return redirect('teacher_dashboard')

        # Get student
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

        # Update session for next subject
        submitted_subjects = Grade.objects.filter(student=student).values_list('subject', flat=True)
        next_subject = None
        for subj in SUBJECT_LIST:
            if subj not in submitted_subjects:
                next_subject = subj
                break

        if next_subject is None:
            # Move to next student
            students = list(Student.objects.order_by('roll_number'))
            try:
                current_index = next(i for i, s in enumerate(students) if s.roll_number == roll_number)
                if current_index + 1 < len(students):
                    request.session['current_student_roll'] = students[current_index + 1].roll_number
                else:
                    request.session['current_student_roll'] = None
            except StopIteration:
                request.session['current_student_roll'] = None

    return redirect('teacher_dashboard')
