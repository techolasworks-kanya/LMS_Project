from datetime import date
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
    number_of_installments = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.course_name

from django.core.validators import MinLengthValidator


class Enquiry(models.Model):
    student_name = models.CharField(max_length=100,null=True, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=100,null=True, blank=True)
    occupation = models.CharField(max_length=100,blank=True, null=True)
    phone1 = models.CharField(max_length=15)
    phone2 = models.CharField(max_length=15, blank=True, null=True)
    enquiry_date = models.DateField(default=date.today)

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
        ('walk in', 'walk in'),
        ('call', 'call'),
        ('referral', 'referral'),
        ('social media', 'social media'),
        ('website', 'website'),
        ('news paper', 'news paper'),
        ('other', 'other'),
    ]
    heard_from = models.CharField(max_length=20, choices=HEARD_FROM_CHOICES, default='walk in')
    course_interested = models.ForeignKey(course, on_delete=models.CASCADE,null=True, blank=True)
    FLEXIBLE_TIMINGS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('both', 'Both'),
       
    ]
    flexible_timings = models.CharField(max_length=10, choices=FLEXIBLE_TIMINGS_CHOICES, blank=True, null=True)
    is_archived = models.BooleanField(default=False, db_index=True)

    # def __str__(self):
    #     return self.student_name
    def __str__(self):
        return self.student_name or f"Enquiry #{self.pk or 'NEW'}"


class EnquiryArchive(models.Model):
    # NO ForeignKey to Enquiry → completely independent!
    student_name = models.CharField(max_length=100,null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=100, null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    phone1 = models.CharField(max_length=15, db_index=True)  # for search
    phone2 = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male','Male'),('female','Female'),('other','Other')], blank=True, null=True)
    educational_qualification = models.CharField(max_length=200, null=True, blank=True)
    university_college = models.CharField(max_length=200, null=True, blank=True)
    percentage = models.FloatField(blank=True, null=True)
    year_of_passing = models.IntegerField(blank=True, null=True)
    
    heard_from = models.CharField(max_length=20, default='walk in', blank=True, null=True)
    course_interested = models.CharField(max_length=100, null=True, blank=True)  # store name only
    flexible_timings = models.CharField(max_length=10, blank=True, null=True)
    
    enquiry_date = models.DateTimeField(default=date.today)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Track final status
    final_status = models.CharField( max_length=30,
        choices=[
            ('new', 'New Enquiry'),
            ('followup', 'In Follow-up'),
            ('admitted', 'Admitted'),
            ('not_interested', 'Not Interested'),
            ('lost', 'Lost Lead'),
        ],
        default='new'
    )

    class Meta:
        verbose_name_plural = "Permanent Enquiry Archives"
        ordering = ['-archived_at']
        indexes = [
            models.Index(fields=['phone1']),
            models.Index(fields=['student_name']),
            models.Index(fields=['enquiry_date']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.phone1} - {self.final_status}"



#follow-up actions
from django.utils import timezone
class FollowUps(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE,related_name='follow_up_actions')
    followup_date = models.DateField(auto_now_add=True, editable=False)
    enquiry_source = models.CharField(max_length=20, editable=False)
    guardian_occupation = models.CharField(max_length=100, blank=True, null=True)

    STATUS_CHOICES = [
        ('new', 'New'),
        ('hot_lead', 'Hot Lead'),
        ('interested', 'Interested'),
        ('not_interested', 'Not Interested'),
        ('contacted', 'Contacted'),
        ('in_discussion', 'In Discussion')
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


from django.core.validators import RegexValidator

class Admission(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE,null=True,related_name='admissions')
    admission_date = models.DateField(default=date.today)
    course = models.ForeignKey('course', on_delete=models.SET_NULL,null=True, blank=True)
    fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20,choices=[('under review', 'Under Review'),('confirmed', 'Confirmed'),('pending', 'Pending'),('under screening', 'Under Screening'),],default='pending')
    is_deleted = models.BooleanField(default=False)
    student_code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    COURSE_CODE_MAPPING = {
   'Data Science': 'DS',
   'Data Analytics': 'DA',
   'Software Testing': 'ST',
   'Python Full Stack':'PFS',
   'Mearn Stack':'MS',
   'Business Analytics': 'BA'
    }
    @staticmethod
    def get_course_code(course_name):
        """Return short code from course name (case-insensitive & flexible)"""
        if not course_name:
            return "NA"

        # Normalize
        normalized = course_name.lower().replace(" ", "").replace("-", "")

        # Exact or partial match in mapping
        for key, code in Admission.COURSE_CODE_MAPPING.items():
            key_clean = key.lower().replace(" ", "").replace("-", "")
            if key_clean in normalized or normalized in key_clean:
                return code

        # Fallback: generate from name
        words = [w for w in course_name.split() if w]
        if len(words) == 1:
            return course_name[:3].upper()
        else:
            return ''.join(word[0].upper() for word in words[:4])[:4]
    

    student_photo = models.ImageField(upload_to='admissions/certificates',null=True,blank=True,help_text="Upload student passport size photo")
    aadhaar_number = models.CharField(max_length=12,null=True,blank=True,unique=True,validators=[RegexValidator(r'^\d{12}$', 'Aadhaar must be exactly 12 digits')],help_text="Enter 12-digit Aadhaar number")
    aadhaar_copy = models.FileField(upload_to='admissions/certificates/aadhaar',null=True,blank=True,help_text="Upload Aadhaar card copy (PDF/Image)")
    educational_certificate = models.FileField(upload_to='admissions/certificates',null=True,blank=True,help_text="Upload 10th/12th/Degree certificate (PDF/Image)")
    SCHEDULE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]
    class_schedule = models.CharField(max_length=10,choices=SCHEDULE_CHOICES,null=True,blank=True,help_text="Select Online or Offline")
    ONLINE_TIMING_CHOICES = [
        ('morning', 'Morning (10:00 AM - 1:00 PM)'),
        ('evening', 'Evening (6:00 PM - 9:00 PM)'),
    ]
    OFFLINE_TIMING_CHOICES = [
        ('9:00 to 11:00', '9:00 AM - 11:00 AM'),
        ('11:00to 1:00', '11:00 AM - 1:00 PM'),
        ('2:00 to 4:00', '2:00 PM - 4:00 PM'),
    ]
    class_timing = models.CharField(max_length=20,null=True,blank=True,help_text="Select timing based on schedule type")
    
    NACTIT_CHOICES = [
        ('yes', 'yes'),
        ('no', 'no'),
    ]
    interested_in_nactet = models.CharField( max_length=5,choices=NACTIT_CHOICES,default='no',help_text="Is student interested in NACTIT exam?")
    nactet_fee = models.DecimalField(max_digits=8,decimal_places=2,default=0.00,editable=False,help_text="₹1000 added if interested in NACTIT"
    )
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    class Meta:
        verbose_name_plural = "Admissions"
        ordering = ['-admission_date']


    def __str__(self):
        if self.enquiry and self.enquiry.student_name:
            return f"Admission: {self.enquiry.student_name} - {self.course or 'No Course'}"
        return f"Admission ID: {self.id} (Student Deleted)"

    def save(self, *args, **kwargs):
        
        self.nactet_fee = 1000.00 if getattr(self, 'interested_in_nactet', 'no') == 'yes' else 0.00

        super().save(*args, **kwargs)



class NotInterestedLead(models.Model):
    followup = models.ForeignKey(FollowUps, on_delete=models.SET_NULL,null=True, blank=True,related_name='not_interested_lead')
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
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    module = models.CharField(max_length=20, choices=MODULE_CHOICES,null=True, blank=True)
    auto_expire_at = models.DateTimeField(null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.content[:50]}... ({'Read' if self.is_read else 'Unread'})"




class Payment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('cash', 'cash'),
        ('upi', 'upi'),
        ('card', 'card'),
        ('bank transfer','bank transfer'),
    ]

    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='payments')
   
    total_fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    RECEIPT_TYPE_CHOICES = [
        ('print receipt', 'print receipt'),
        ('email receipt', 'email receipt'),
        ('both', 'both')
    ]

    receipt_type = models.CharField(max_length=20, choices=RECEIPT_TYPE_CHOICES, default='print receipt')


    class Meta:
        verbose_name_plural = "Payments"
        ordering = ['-payment_date']


    def save(self, *args, **kwargs):
        if not self.receipt_number:
            date_str = timezone.now().strftime('%Y%m%d')
            count = Payment.objects.filter(payment_date__date=timezone.now().date()).count() + 1
            self.receipt_number = f"REC-{date_str}{count:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number
    













