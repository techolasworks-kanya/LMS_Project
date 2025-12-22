from LMS_app.serializers import *
from LMS_app.models import *
from rest_framework import serializers


#give a batch id  field -   without values
class DataForFinanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='admission.enquiry.student_name', read_only=True)
    course_name = serializers.CharField(source='admission.course.course_name', read_only=True)
    no_of_course_installments = serializers.IntegerField(source='admission.course.number_of_installments', read_only=True,allow_null=True)
    phone_number = serializers.CharField(source='admission.enquiry.phone1', read_only=True)
    student_code = serializers.CharField(source='admission.student_code', read_only=True)
    
    payment_mode = serializers.CharField(read_only=True)
    payment_structure = serializers.CharField(read_only=True)
    batch_id = serializers.IntegerField( read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = [
            'student_code',
            'student_name',
            'course_name',
            'no_of_course_installments',
            'phone_number',
            'total_fee_amount',
            'payment_mode',
            'payment_structure',
            'batch_id',
        ]
        