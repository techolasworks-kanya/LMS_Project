from rest_framework import serializers
from .models import course, Enquiry, certfication

class CertficationSerializer(serializers.ModelSerializer):
    class Meta:
        model = certfication
        fields = '__all__'


        
class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = course
        fields = '__all__'

class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = course
        fields = ['course_name', 'duration', 'course_fee']
        

class EnquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'

class EnquiryListSerializer(serializers.ModelSerializer):
     class Meta:
        model = Enquiry
        fields = [ 'student_name', 'enquiry_date', 'course_interested','heard_from','action']
        # extra_kwargs = {
        #     'student_name': {'required': True},
        #     'date_of_birth': {'required': True},  
        #     'guardian_name': {'required': True},  
            
        # } 

