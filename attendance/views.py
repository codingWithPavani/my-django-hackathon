# import json
# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import JsonResponse
# from django.contrib.auth.decorators import login_required
# from .models import Student, Attendance, Grade
# from django.views.decorators.http import require_POST
# from django.utils.dateparse import parse_date
# from django.contrib import messages

# @login_required
# def teacher_dashboard(request):
#     if not request.user.is_staff:
#         return redirect('student_dashboard')
    
#     students = Student.objects.all().order_by('roll_number')

#     # Optional: add attendance and grade info
#     for s in students:
#         latest_att = Attendance.objects.filter(student=s).order_by('-date').first()
#         latest_grade = Grade.objects.filter(student=s).order_by('-id').first()
#         s.attendance_status = latest_att.status if latest_att else "N/A"
#         s.grade_value = latest_grade.marks if latest_grade else "N/A"

#     return render(request, 'attendance/teacher_dashboard.html', {'students': students})


# @login_required
# def save_attendance(request):
#     if request.method == 'POST':
#         roll_number = request.POST.get('roll_number')
#         attendance_status = request.POST.get('attendance')

#         try:
#             student = Student.objects.get(roll_number=roll_number)
#             Attendance.objects.update_or_create(
#                 student=student,
#                 date=parse_date(str(request.POST.get('date', '2025-08-12'))),
#                 defaults={'status': attendance_status}
#             )
#             messages.success(request, f"Attendance saved for {student.user.get_full_name()}")
#         except Student.DoesNotExist:
#             messages.error(request, f"Student with Roll No {roll_number} not found")

#     return redirect('teacher_dashboard')



# @require_POST
# @login_required
# def mark_attendance(request):
#     if not request.user.is_staff:
#         return JsonResponse({'error': 'forbidden'}, status=403)
#     data = json.loads(request.body)
#     date_str = data.get('date')
#     records = data.get('records', [])
#     date = parse_date(date_str)
#     for r in records:
#         student_id = r.get('student_id')
#         status = r.get('status')
#         try:
#             stu = Student.objects.get(pk=student_id)
#             Attendance.objects.update_or_create(
#                 student=stu, date=date,
#                 defaults={'status': status}
#             )
#         except Student.DoesNotExist:
#             continue
#     return JsonResponse({'ok': True})

# @require_POST
# @login_required
# def enter_grade(request):
#     if request.method == 'POST':
#         roll_number = request.POST.get("roll_number")
#         grade = request.POST.get("grade")
#         subject = request.POST.get("subject", "General")

#         try:
#             student = Student.objects.get(roll_number=roll_number)
#             Grade.objects.create(student=student, subject=subject, marks=int(grade))
#             messages.success(request, f"Grade saved for {student.user.get_full_name()}")
#         except Student.DoesNotExist:
#             messages.error(request, f"Student with Roll No {roll_number} not found")
#         except ValueError:
#             messages.error(request, "Grade must be a number")

#     return redirect('teacher_dashboard')



# @login_required
# def student_dashboard(request):
#     if request.user.is_staff:
#         return redirect('teacher_dashboard')
#     student = get_object_or_404(Student, user=request.user)
#     attendance_qs = Attendance.objects.filter(student=student).order_by('date')
#     total = attendance_qs.count()
#     present = attendance_qs.filter(status='Present').count()
#     absent = total - present
#     grades = Grade.objects.filter(student=student)
#     return render(request, 'attendance/student_dashboard.html', {
#         'student': student,
#         'attendance_total': total,
#         'attendance_present': present,
#         'attendance_absent': absent,
#         'grades': grades,
#     })


# attendance/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.dateparse import parse_date
from .models import Student, Attendance, Grade
from datetime import date

@login_required
def redirect_user(request):
    """Redirect users based on role."""
    if request.user.is_staff:
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')

@login_required
def teacher_dashboard(request):
    if not request.user.is_staff:
        return redirect('student_dashboard')

    # Fetch students
    students = list(Student.objects.select_related('user').all().order_by('roll_number'))

    # Build quick lookup for latest attendance and latest grade
    # (Note: small N, ok to do this way for hackathon)
    latest_att_map = {}
    for att in Attendance.objects.order_by('-date'):
        sid = att.student_id
        if sid not in latest_att_map:
            latest_att_map[sid] = att.status

    latest_grade_map = {}
    for g in Grade.objects.order_by('-created_at'):
        sid = g.student_id
        if sid not in latest_grade_map:
            latest_grade_map[sid] = g.marks

    # Attach attributes to student objects for template
    for s in students:
        s.attendance_status = latest_att_map.get(s.id, "N/A")
        s.grade_value = latest_grade_map.get(s.id, "N/A")

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

@login_required
def save_grade(request):
    """
    Handles form POST:
    - expects 'roll_number', 'subject' (optional) and 'marks'
    """
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number', '').strip()
        subject = request.POST.get('subject', 'General').strip()
        marks = request.POST.get('marks', '').strip()

        if not roll_number or marks == '':
            messages.error(request, "Roll number and marks are required.")
            return redirect('teacher_dashboard')

        try:
            student = Student.objects.get(roll_number=roll_number)
        except Student.DoesNotExist:
            messages.error(request, f"Student with roll {roll_number} not found.")
            return redirect('teacher_dashboard')

        try:
            marks_int = int(marks)
        except ValueError:
            messages.error(request, "Marks must be an integer.")
            return redirect('teacher_dashboard')

        Grade.objects.create(student=student, subject=subject, marks=marks_int)
        messages.success(request, f"Grade ({marks_int}) saved for {student.user.get_full_name() or student.user.username}.")

    return redirect('teacher_dashboard')

@login_required
def student_dashboard(request):
    if request.user.is_staff:
        return redirect('teacher_dashboard')

    student = get_object_or_404(Student, user=request.user)
    attendance_qs = Attendance.objects.filter(student=student).order_by('date')
    total = attendance_qs.count()
    present = attendance_qs.filter(status='Present').count()
    absent = total - present
    grades = Grade.objects.filter(student=student).order_by('-created_at')[:20]

    return render(request, 'attendance/student_dashboard.html', {
        'student': student,
        'attendance_total': total,
        'attendance_present': present,
        'attendance_absent': absent,
        'grades': grades,
    })
