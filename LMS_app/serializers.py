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
        
# class EnquiryCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Enquiry
#         fields = '__all__'
#         extra_kwargs = {
#             'student_name':          {'required': True},
#             'phone1':                {'required': True},
#             'educational_qualification': {'required': True},
#             'heard_from':            {'required': True},
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         required = set(self.Meta.extra_kwargs.keys())
#         for name, field in self.fields.items():
#             if name not in required:
#                 field.required = False
#                 field.allow_blank = True
#                 field.allow_null = True

#     # Override to_cleaned_data to convert empty strings to None
#     def to_internal_value(self, data):
#         # Make a mutable copy
#         data = data.copy()

#         # List of fields that should be null if blank
#         nullable_fields = [
#             'occupation', 'phone2', 'address', 'gender',
#             'university_college', 'percentage', 'year_of_passing',
#             'flexible_timings', 'course_interested','date_of_birth','guardian_name'

#         ]

#         for field in nullable_fields:
#             if field in data:
#                 value = data[field]
#                 if value == '' or value is None:
#                     data[field] = None
#                 else:
#                     data[field] = value

#         return super().to_internal_value(data)
class EnquiryCreateSerializer(serializers.ModelSerializer):
    course_interested_input = serializers.CharField(
        source='course_interested',  required=False,
        allow_blank=True,
        write_only=True,
        help_text="Course name or"
    )

    class Meta:
        model = Enquiry
        fields = '__all__'
        extra_kwargs = {
            'student_name': {'required': True},
            'phone1': {'required': True},
            'educational_qualification': {'required': True},
            'heard_from': {'required': True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required = {'student_name', 'phone1', 'educational_qualification', 'heard_from'}
        for name, field in self.fields.items():
            if name not in required:
                field.required = False
                field.allow_blank = True
                field.allow_null = True

    def to_internal_value(self, data):
        data = data.copy()

        nullable_fields = [
            'occupation', 'phone2', 'address', 'gender',
            'university_college', 'percentage', 'year_of_passing',
            'flexible_timings', 'date_of_birth', 'guardian_name', 'email'
        ]
        for f in nullable_fields:
            if f in data and data[f] in ['', None]:
                data[f] = None

        raw_course = data.pop('course_interested_input', None)

        if raw_course is not None:
            raw_course = str(raw_course).strip()

            if raw_course == '':
                data['course_interested'] = None
            else:
                if raw_course.isdigit():
                    try:
                        course_obj = course.objects.get(pk=int(raw_course))
                        data['course_interested'] = course_obj
                    except course.DoesNotExist:
                        raise serializers.ValidationError({
                            'course_interested_input': f'Course with ID {raw_course} not found.'
                        })
                else:
                    try:
                        course_obj = course.objects.get(course_name__iexact=raw_course)
                        data['course_interested'] = course_obj
                    except course.DoesNotExist:
                        raise serializers.ValidationError({
                            'course_interested_input': f'Course "{raw_course}" not found.'
                        })

        return super().to_internal_value(data)

        
class EnquiryListSerializer(serializers.ModelSerializer):
  
    course_interested = serializers.CharField(
        source='course_interested.course_name',  
        read_only=True,
        allow_null=True
    )
    enquiry_date = serializers.DateField(format='%d-%m-%Y',  input_formats=['%Y-%m-%d'], read_only=True)

    class Meta:
        model = Enquiry
        fields = [
            'id',
            'student_name',
            'enquiry_date',
            'course_interested',   
            'heard_from',
        ]
        


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
    



class FollowUpListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='enquiry.student_name', read_only=True)
    course_interested = serializers.CharField(
        source='enquiry.course_interested.course_name',
        read_only=True,
        allow_null=True
    )
    enquiry_date = serializers.DateField(source='enquiry.enquiry_date', read_only=True)
    # source_of_enquiry = serializers.CharField(source='enquiry.heard_from', read_only=True)

    class Meta:
        model = FollowUps
        fields = [
            'id',
            'student_name',
            'course_interested',
            'enquiry_date',
            # 'source_of_enquiry',
            'status',
            # 'followup_date',
            'next_followup_date',
        ]

# 2. Detail / Create / Update – full enquiry data + follow-up fields

class FollowUpDetailSerializer(serializers.ModelSerializer):
    enquiry_data = serializers.SerializerMethodField()

    class Meta:
        model = FollowUps
        fields = [
            'id',
            'enquiry',
            'enquiry_data',
            'followup_date',
            'status',
            'remarks',
            'next_followup_date',
        ]
        read_only_fields = ('followup_date', 'enquiry_data')

    def get_enquiry_data(self, obj):
        e = obj.enquiry
        return {
            "student_name": e.student_name,
            "course_interested": e.course_interested.course_name if e.course_interested else None,
            "enquiry_date": e.enquiry_date,
            "heard_from": e.heard_from,
            # add more as needed
        }

    # Make 'enquiry' read-only only during update
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['enquiry'].read_only = True
            self.fields['enquiry'].required = False