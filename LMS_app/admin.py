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
    list_per_page = 50

    def get_queryset(self, request):
        # This already reduces queries a lot
        return super().get_queryset(request).select_related('course_interested').prefetch_related('admissions', 'follow_up_actions')

    def status_tag(self, obj):
        # Super fast version – no extra DB query because we prefetched above
        if obj.admissions and obj.admissions.exists():
            return "ADMITTED"
        elif obj.follow_up_actions and obj.follow_up_actions.exists():
            return "IN FOLLOW-UP"
        else:
            return "NEW"

    # THESE TWO LINES ARE MANDATORY – THIS IS WHAT FIXES THE CRASH
    status_tag.short_description = "Status"
    status_tag.admin_order_field = 'enquiry_date'   # optional, allows sorting

admin.site.register(EnquiryArchive)
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
admin.site.register(Payment)

 