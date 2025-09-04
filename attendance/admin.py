from django.contrib import admin
from .models import Student, Attendance, Grade

admin.site.register(Student)
admin.site.register(Attendance)
admin.site.register(Grade)

