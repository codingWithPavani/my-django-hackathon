# attendance/models.py (your version — keep it)
from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20)
    course = models.CharField(max_length=100, blank=True, null=True)
    CD = models.IntegerField( blank=True, null=True)
    DWDM = models.IntegerField(blank=True, null=True)
    OOAD = models.IntegerField(blank=True, null=True)
    DAA = models.IntegerField(blank=True, null=True)
    IoT = models.IntegerField(blank=True, null=True)


    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.roll_number})"      
    

class Attendance(models.Model):
    STATUS_CHOICES = [("Present","Present"), ("Absent","Absent")]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=7, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ("student", "date")
EXAM_CHOICES = [
    ('mid1', 'Mid 1'),
    ('mid2', 'Mid 2'),
    ('final', 'Final Exam'),
]
class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE )
    subject = models.CharField(max_length=100)
    # mid1_marks = models.IntegerField(null=True, blank=True)
    # mid2_marks = models.IntegerField(null=True, blank=True)
    # sem_marks = models.IntegerField(null=True, blank=True)
    # exam_type = models.CharField(max_length=20, choices=[("Mid1", "Mid1"), ("Mid2", "Mid2"), ("Semester", "Semester")])
    marks = models.IntegerField()
    exam_type = models.CharField(max_length=10, choices=EXAM_CHOICES, default='mid1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam_type')

    def __str__(self):
        return f"{self.student.roll_number} - {self.subject} ({self.exam_type})"
