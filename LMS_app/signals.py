from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Enquiry, EnquiryArchive, FollowUps, Admission

@receiver(post_save, sender=Enquiry)
def archive_enquiry_on_create(sender, instance, created, **kwargs):
    if created:
        EnquiryArchive.objects.create(
            student_name=instance.student_name,
            date_of_birth=instance.date_of_birth,
            guardian_name=instance.guardian_name,
            occupation=instance.occupation,
            phone1=instance.phone1,
            phone2=instance.phone2,
            email=instance.email,
            address=instance.address,
            gender=instance.gender,
            educational_qualification=instance.educational_qualification,
            university_college=instance.university_college,
            percentage=instance.percentage,
            year_of_passing=instance.year_of_passing,
            heard_from=instance.heard_from,
            course_interested=instance.course_interested.course_name if instance.course_interested else "Not Selected",
            flexible_timings=instance.flexible_timings,
            enquiry_date=instance.enquiry_date,
            final_status='new'
        )