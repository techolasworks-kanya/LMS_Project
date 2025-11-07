from rest_framework import serializers
from .models import *

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
        extra_kwargs = {
            'student_name':          {'required': True},
            'date_of_birth':         {'required': True},
            'guardian_name':         {'required': True},
            'phone1':                {'required': True},
            'email':                 {'required': True},
            'educational_qualification': {'required': True},
            'heard_from':            {'required': True},
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
        fields = ['student_name', 'enquiry_date', 'course_interested',
                  'heard_from']
        


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Auto-generated. Cannot be set manually."
    )

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'job_title', 'password']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
            'job_title': {'required': True},
        }

    def validate_password(self, value):
        raise serializers.ValidationError("Password cannot be set manually. It is auto-generated.")

    def create(self, validated_data):
        validated_data.pop('password', None)
        email = validated_data['email']
        name = validated_data['name']
        job_title = validated_data['job_title']

        # Auto-generate secure password
        password = CustomUser.generate_password()

        # Create user
        is_staff = True if job_title.lower() == 'admin' else False

        user = CustomUser.objects.create_user(
            username=email,
            email=email,
            name=name,
            job_title=job_title,
            password=password,
            is_staff=is_staff
        )
        user.temp_password = password
        return user