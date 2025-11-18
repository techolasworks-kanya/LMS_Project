from django.contrib import admin
from .models import *
from django.db.models import Q

# Register your models here.
admin.site.register(certfication)
admin.site.register(course)
@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'phone1', 'course_interested', 'enquiry_date', 'status_tag']
    search_fields = ['student_name', 'phone1', 'email']
    list_filter = ['enquiry_date', 'course_interested']
    ordering = ['-enquiry_date']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Hide enquiries that have EVER been converted to admission (even if admission was deleted)
        return qs.filter(
            Q(admissions__isnull=True) & Q(follow_up_actions__isnull=True)
        ).distinct()

    def status_tag(self, obj):
        if obj.admissions.exists():
            return "ADMITTED"
        elif obj.follow_up_actions.exists():
            return "IN FOLLOW-UP"
        else:
            return "NEW"
    status_tag.short_description = "Status"


    
admin.site.register(FollowUps)
admin.site.register(FollowUpRemark)
admin.site.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'admission_date', 'get_student_name', 'course', 'status', 'fee_paid']
    search_fields = ['enquiry__student_name', 'enquiry__phone1']
    list_filter = ['admission_date', 'status']

    def get_student_name(self, obj):
        return obj.enquiry.student_name if obj.enquiry else "— (Deleted Student)"
    get_student_name.short_description = "Student Name"




admin.site.register(NotInterestedLead)

admin.site.register(Notification)

 