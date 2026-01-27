from django.db import models
from LMS_app.models import*
from django.core.exceptions import ValidationError

class Fee_Collection(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)

    PAYMENT_STRUCTURE_CHOICES = [
        ('One time', 'One time'),
        ('installments', 'installments'),
       
    ]

    payment_structure = models.CharField(max_length=20,choices=PAYMENT_STRUCTURE_CHOICES,null=True,blank=True,help_text="How student will pay fees")
    elegible_for_discount = models.CharField(max_length=10,choices=[('yes', 'yes'), ('no', 'no')],default='no')
    discount_type = models.CharField(max_length=10,choices=[('refferel', 'refferel'), ('webinar', 'webinar'), ('one time', 'one time')])
    webinar_application_timing = models.CharField(max_length=20,choices=[
            ('last_2_hours', 'Applied within the last 2 hours'),
            ('before_4pm', 'Applied before 4 PM the next day'),],blank=True,null=True)
    
    no_of_refferal = models.IntegerField(default=0)
    refferal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    installment_number = models.PositiveIntegerField(null=True,blank=True,help_text="Which installment is being paid (e.g., 1, 2, 3...)")
    installment_amount = models.DecimalField(max_digits=10,decimal_places=2, null=True,blank=True,help_text="Amount paid for this specific installment")

    total_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    total_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    payment_mode = models.CharField(max_length=20,choices=[('cash', 'cash'), ('upi', 'upi'), ('card', 'card'), ('bank transfer', 'bank transfer')],default='cash')

    payment_status = models.CharField(max_length=20, choices=[     ('pending', 'Pending'),     ('completed', 'Completed'),    ('failed', 'Failed') ], default='completed', help_text="Payment completion status")
    qr_code_id = models.CharField(max_length=50, null=True, blank=True)
    razorpay_qr_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def clean(self):
        if self.installment_number is not None and self.installment_number < 1:
            raise ValidationError({'installment_number': 'Must be positive.'})
        super().clean()

    def __str__(self):
        return f"{self.payment.admission.student_code} - {self.payment_mode} - {self.payment_status}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Fee Collection"
        verbose_name_plural = "Fee Collections"

    




    

                                             



# # Create your models here.
