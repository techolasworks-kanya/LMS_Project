from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class certfication(models.Model):
    certfication_name = models.CharField(max_length=100)

    def __str__(self):
        return self.certfication_name

class course(models.Model):
    course_name = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    course_fee = models.DecimalField(max_digits=10, decimal_places=2)
    certfication = models.ForeignKey(certfication, on_delete=models.CASCADE, null=True, blank=True)
    course_syllabus=models.FileField(upload_to='uploads/', null=True, blank=True) 

    def __str__(self):
        return self.course_name
class Enquiry(models.Model):
    student_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    guardian_name = models.CharField(max_length=100)
    occupation = models.CharField(max_length=100)
    phone1 = models.CharField(max_length=15)
    phone2 = models.CharField(max_length=15, blank=True, null=True)
    enquiry_date = models.DateField(auto_now_add=True)

    email = models.EmailField()
    address = models.TextField()
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    educational_qualification = models.CharField(max_length=200)
    university_college = models.CharField(max_length=200)
    percentage = models.FloatField()
    year_of_passing = models.IntegerField()
    HEARD_FROM_CHOICES = [
        ('walk in', 'Walk-in'),
        ('call', 'Call'),
        ('referral', 'Referral'),
        ('social media', 'Social Media'),
    ]
    heard_from = models.CharField(max_length=20, choices=HEARD_FROM_CHOICES, default='walk in')
    course_interested = models.ForeignKey(course, on_delete=models.CASCADE)
    FLEXIBLE_TIMINGS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('both', 'Both'),
       
    ]
    flexible_timings = models.CharField(max_length=10, choices=FLEXIBLE_TIMINGS_CHOICES, blank=True, null=True)
    ACTION_CHOICES = [
        ('follow up', 'Follow Up'),
        ('admission', 'Admission'),
        ('not interested', 'Not Interested'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='follow up')

    def __str__(self):
        return self.student_name

    

   