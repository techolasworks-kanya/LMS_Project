
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
# class Command(BaseCommand):
#     help = 'Creates demo data for November 2025 only (20 enquiries, 12 admissions)'

#     def handle(self, *args, **options):
#         # Correct imports – note: your model class is named "course" (lowercase!)
#         from LMS_app.models import course as CourseModel, Enquiry, Admission

#         self.stdout.write("Checking if November demo data already exists...")

#         if Enquiry.objects.filter(student_name__icontains="Nov Student").exists():
#             self.stdout.write(
#                 self.style.WARNING("November demo data already exists! Skipping.")
#             )
#             return

#         # Create or get the course (model class name is lowercase "course")
#         course_obj, created = CourseModel.objects.get_or_create(
#             course_name="Data Science",
#             defaults={
#                 'course_fee': 45000.00,
#                 'duration': '6 Months',
#                 # Add other required fields if you have them (e.g. certfication=None)
#             }
#         )

#         if created:
#             self.stdout.write("Created course: Data Science")
#         else:
#             self.stdout.write("Using existing course: Data Science")

#         # Optional cleanup
#         Enquiry.objects.filter(student_name__icontains="Test Student").delete()

#         created_count = 0
#         converted_count = 0
#         base_date = date(2025, 11, 15)

#         for i in range(1, 21):
#             # Spread enquiries across November
#             days_offset = (20 - i) * 1.4  # nice spread
#             enquiry_date = base_date - timedelta(days=days_offset)

#             enquiry = Enquiry.objects.create(
#                 student_name=f"Nov Student {i}",
#                 phone1="99999" + f"{10000 + i}"[-5:],
#                 educational_qualification="B.Tech",
#                 enquiry_date=enquiry_date,
#                 course_interested=course_obj,
#                 heard_from='walk in',
#                 gender='male',  # required field
#                 occupation="Student",
#                 guardian_name="Parent"
#             )

#             # Convert first 12 to admissions
#             if i <= 12:
#                 admission_date = enquiry_date + timedelta(days=2)

#                 Admission.objects.create(
#                     enquiry=enquiry,
#                     course=course_obj,
#                     admission_date=admission_date,
#                     status='confirmed',
#                     fee_paid=10000.00,
#                     admission_fee=2000.00,  # common field
#                     payment_structure='full',
#                     class_schedule='offline',
#                     interested_in_nactet='no'
#                     # no total_fee → removed!
#                 )
#                 converted_count += 1

#             created_count += 1

#         self.stdout.write(
#             self.style.SUCCESS(
#                 f"Demo data created: {created_count} enquiries, {converted_count} confirmed admissions (November 2025)"
#             )
#         )
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
                student_name=f"Nov Student {i}",
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

            # Create Admission for first 12 students
            if i <= 12:
                admission_date = enquiry_date + timedelta(days=2)

                Admission.objects.create(
                    enquiry=enquiry,                    # ← Correct: pass the object
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