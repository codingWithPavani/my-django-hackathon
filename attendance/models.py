# from django.db import models
# from django.contrib.auth.models import User

# class Student(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     roll_number = models.CharField(max_length=20)
#     course = models.CharField(max_length=100, blank=True)

#     def __str__(self):
#         return f"{self.user.get_full_name() or self.user.username} ({self.roll_number})"

# class Attendance(models.Model):
#     STATUS_CHOICES = [("Present","Present"), ("Absent","Absent")]
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     date = models.DateField()
#     status = models.CharField(max_length=7, choices=STATUS_CHOICES)

#     class Meta:
#         unique_together = ("student", "date")

# class Grade(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     subject = models.CharField(max_length=100)
#     marks = models.PositiveIntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)


# attendance/models.py (your version — keep it)
from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20)
    course = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.roll_number})"

class Attendance(models.Model):
    STATUS_CHOICES = [("Present","Present"), ("Absent","Absent")]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=7, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ("student", "date")

class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    marks = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
