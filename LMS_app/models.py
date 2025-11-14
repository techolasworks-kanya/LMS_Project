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
    course_name = models.CharField(max_length=100, unique=True)
    duration = models.CharField(max_length=50)
    course_fee = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
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
from django.utils import timezone
class FollowUps(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE,
                                related_name='follow_up_actions')
    followup_date = models.DateField(auto_now_add=True, editable=False)
    enquiry_source = models.CharField(max_length=20, editable=False)
    guardian_occupation = models.CharField(max_length=100, blank=True, null=True)

    STATUS_CHOICES = [
        ('new', 'New'),
        ('hot_lead', 'Hot Lead'),
        ('interested', 'Interested'),
        ('not_interested', 'Not Interested'),
        ('contacted', 'Contacted'),
        ('indiscussion', 'In Discussion')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='new')
    next_followup_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Follow Ups"
        ordering = ['-followup_date']

    def __str__(self):
        return f"Follow-up for {self.enquiry.student_name} on {self.followup_date}"
    

class FollowUpRemark(models.Model):
    followup = models.ForeignKey('FollowUps',on_delete=models.CASCADE,related_name='remarks')
    content = models.TextField()
    added_on = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['-added_on']

    def __str__(self):
        return f"{self.content[:30]}... ({self.added_on.strftime('%d/%m/%Y, %I:%M %p')})"





class Admission(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE,related_name='admissions')
    admission_date = models.DateField(auto_now_add=True)
    course = models.ForeignKey('course', on_delete=models.SET_NULL,null=True, blank=True)
    fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20,choices=[('confirmed', 'Confirmed'),('pending', 'Pending'),('cancelled', 'Cancelled'),],default='pending')

    class Meta:
        verbose_name_plural = "Admissions"
        ordering = ['-admission_date']

    def __str__(self):
        return f"Admission: {self.enquiry.student_name} - {self.course}"
    

class NotInterestedLead(models.Model):
    followup = models.ForeignKey(FollowUps, on_delete=models.CASCADE,null=True, blank=True,related_name='not_interested_lead')
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE,related_name='not_interested_records')
    last_followup_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20,
choices=[
            ('not_interested', 'Not Interested'),
            ('rejected', 'Rejected'),
            ('follow_up', 'Follow Up'),
        ],
        default='not_interested'
    )
    archived_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Not Interested Leads"
        ordering = ['-archived_on']

    def __str__(self):
        return f"{self.enquiry.student_name} - {self.get_status_display()}"




class Notification(models.Model):
    MODULE_CHOICES = [
        ('enquiry', 'Enquiry'),
        ('admission', 'Admission'),
        ('general', 'General'),
    ]

    module = models.CharField(max_length=20, choices=MODULE_CHOICES,null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.content[:50]}... ({'Read' if self.is_read else 'Unread'})"