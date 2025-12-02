
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date

class Command(BaseCommand):
    help = 'Creates demo data for November 2025 only (20 enquiries, 12 admissions)'

    def handle(self, *args, **options):
        from LMS_app.models import course, Enquiry, Admission 

        self.stdout.write("Checking if November demo data already exists...")

        if Enquiry.objects.filter(student_name__icontains="Nov Student").exists():
            self.stdout.write(
                self.style.WARNING("November demo data already exists! Skipping creation.")
            )
            return

        course, created = course.objects.get_or_create(
            course_name="Data Science",
            defaults={
                'course_fee': 45000.00,
                'duration_months': 6
            }
            
        )

        if created:
            self.stdout.write(f"Created course: {course.course_name}")
        else:
            self.stdout.write(f"Using existing course: {course.course_name}")

        Enquiry.objects.filter(student_name__icontains="Test Student").delete()
        Admission.objects.filter(enquiry__student_name__icontains="Test Student").delete()

        nov_date = date(2025, 11, 15)  

        created_count = 0
        converted_count = 0

        for i in range(1, 21):
            enquiry_date = nov_date - timezone.timedelta(days=(20 - i) * 1.5) 

            enquiry = Enquiry.objects.create(
                student_name=f"Nov Student {i}",
                phone1="99999" + str(10000 + i).zfill(5),
                educational_qualification="B.Tech",
                enquiry_date=enquiry_date,
                course_interested=course,
                heard_from='walk in'
            )

            if i <= 12:
                admission_date = enquiry_date + timezone.timedelta(days=2)
                Admission.objects.create(
                    enquiry=enquiry,
                    course=course,
                    admission_date=admission_date,
                    status='confirmed',
                    total_fee=45000,
                    fee_paid=10000  # optional
                )
                converted_count += 1

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} enquiries and {converted_count} admissions for November 2025!"
            )
        )