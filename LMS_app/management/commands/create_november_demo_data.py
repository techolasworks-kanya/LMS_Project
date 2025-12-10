
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Creates 20 demo enquiries + 12 confirmed admissions for November 2025'

    def handle(self, *args, **options):
        from LMS_app.models import course as CourseModel, Enquiry, Admission

        # Stop if already created
        if Enquiry.objects.filter(student_name__icontains="Nov Student").exists():
            self.stdout.write(self.style.WARNING("November demo data already exists! Skipping..."))
            return

        self.stdout.write("Creating 20 enquiries + 12 admissions for November 2025...")

        # Get or create the course
        course_obj, _ = CourseModel.objects.get_or_create(
            course_name="Data Science",
            defaults={
                'course_fee': 45000.00,
                'duration': '6 Months',
            }
        )

        base_date = date(2025, 11, 15)

        enquiries_created = 0
        admissions_created = 0

        for i in range(1, 21):  # 20 students
            offset_days = (20 - i) * 1.5
            enquiry_date = base_date - timedelta(days=offset_days)

            # Create Enquiry
            enquiry = Enquiry.objects.create(
                student_name=f"Student {i}",
                phone1=f"999991{i:04d}",
                educational_qualification="B.Tech",
                enquiry_date=enquiry_date,
                course_interested=course_obj,
                heard_from='walk in',
                gender='male',
                occupation="Student",
                guardian_name=f"Parent of Student {i}",
                email=f"nov{i}@demo.com",
            )
            enquiries_created += 1

            if i <= 12:
                admission_date = enquiry_date + timedelta(days=2)

                Admission.objects.create(
                    enquiry=enquiry,                    
                    course=course_obj,
                    admission_date=admission_date,
                    status='confirmed',
                    fee_paid=15000.00,
                    admission_fee=2000.00,
                    payment_structure='full',
                    class_schedule='offline',
                    interested_in_nactet='no'
                )
                admissions_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"SUCCESS! Created {enquiries_created} enquiries and {admissions_created} admissions!"
            )
        )