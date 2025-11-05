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
        

# class EnquiryCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Enquiry
#         fields = '__all__'
#         extra_kwargs = {
#             'student_name': {'required': True},
#             'date_of_birth': {'required': True},  
#             'guardian_name': {'required': True}, 
#             'phone1' : {'required': True},
#             'qualification': {'required': True},
#             'heard_from':{'required': True},

#             'phone2': {'required': False},
#             'email': {'required': False},
#             'address': {'required': False},
#             'gender': {'required': False},
#             'university_college': {'required': False},
#             'percentage': {'required': False},
#             'year_of_passing': {'required': False},
#             'course_interested': {'required': False},
#             'flexible_timings': {'required': False},
#             'action': {'required': False},
#             'occupation': {'required': False},
            
#         } 
class EnquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'
        extra_kwargs = {
            'student_name': {'required': True},
            'date_of_birth': {'required': True},
            'guardian_name': {'required': True},
            'phone1': {'required': True},
            'educational_qualification': {'required': True},
            'heard_from': {'required': True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-make all other fields optional
        required_fields = self.Meta.extra_kwargs.keys()
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False
                if hasattr(field, 'allow_blank'):
                    field.allow_blank = True

class EnquiryListSerializer(serializers.ModelSerializer):
     class Meta:
        model = Enquiry
        fields = [ 'student_name', 'enquiry_date', 'course_interested','heard_from','action']
        extra_kwargs = {
            'student_name': {'required': True},
            'date_of_birth': {'required': True},  
            'guardian_name': {'required': True}, 
            'phone1' : {'required': True},
            'qualification': {'required': True},
            'heard_from':{'required': True}
            
        } 

