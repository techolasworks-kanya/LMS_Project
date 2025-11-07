from django.db import models
# from django .contrib.auth.models import AbstractUser

from django.contrib.auth.models import AbstractUser
import string
import secrets

class CustomUser(AbstractUser):
   
    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  

    def __str__(self):
        return self.email

    @staticmethod
    def generate_password(length=12):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))
    


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
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=100,null=True, blank=True)
    occupation = models.CharField(max_length=100,blank=True, null=True)
    phone1 = models.CharField(max_length=15)
    phone2 = models.CharField(max_length=15, blank=True, null=True)
    enquiry_date = models.DateField(auto_now_add=True)

    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    educational_qualification = models.CharField(max_length=200)
    university_college = models.CharField(max_length=200, null=True, blank=True)
    percentage = models.FloatField(blank=True, null=True)
    year_of_passing = models.IntegerField(blank=True, null=True)
    HEARD_FROM_CHOICES = [
        ('walk in', 'Walk-in'),
        ('call', 'Call'),
        ('referral', 'Referral'),
        ('social media', 'Social Media'),
        ('website', 'Website')
    ]
    heard_from = models.CharField(max_length=20, choices=HEARD_FROM_CHOICES, default='walk in')
    course_interested = models.ForeignKey(course, on_delete=models.CASCADE,null=True, blank=True)
    FLEXIBLE_TIMINGS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('both', 'Both'),
       
    ]
    flexible_timings = models.CharField(max_length=10, choices=FLEXIBLE_TIMINGS_CHOICES, blank=True, null=True)
    

    def __str__(self):
        return self.student_name

#follow-up actions

# class FollowUpAction(models.Model):
#     enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='follow_up_actions')
#     enquiry_source = models.CharField(max_length=20, editable=False)
#     guardian_occupation = models.CharField(max_length=100, blank=True, null=True)
#     STATUS_CHOICES = [
#         ('new', 'New'),
#         ('hot_lead', 'Hot Lead'),
#         ('not_interested', 'Not Interested'),
#     ]
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
#     remarks = models.TextField(blank=True, null=True)
#     next_followup_date = models.DateField(null=True, blank=True) 

   
    

    def __str__(self):
        return f"Action for {self.enquiry.student_name} on {self.action_date}"