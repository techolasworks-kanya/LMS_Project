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

# class FollowUpDetailSerializer(serializers.ModelSerializer):
#     enquiry_data = serializers.SerializerMethodField()

#     class Meta:
#         model = FollowUps
#         fields = [
#             'id',
#             'enquiry',
#             'enquiry_data',
#             'followup_date',
#             'status',
#             'remarks',
#             'next_followup_date',
#         ]
#         read_only_fields = ('followup_date', 'enquiry_data')

#     def get_enquiry_data(self, obj):
#         e = obj.enquiry
#         return {
#             "student_name": e.student_name,
#             "course_interested": e.course_interested.course_name if e.course_interested else None,
#             "enquiry_date": e.enquiry_date,
#             "heard_from": e.heard_from,
#         }

#     # Make 'enquiry' read-only only during update
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if self.instance:
#             self.fields['enquiry'].read_only = True
#             self.fields['enquiry'].required = False
class EnquiryNestedUpdateSerializer(serializers.ModelSerializer):
    course_interested_input = serializers.CharField(
        source='course_interested',
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Course name (e.g. 'Python Full Stack') or ID (e.g. 5)"
    )

    class Meta:
        model = Enquiry
        fields = [
            'student_name', 'date_of_birth', 'guardian_name', 'occupation',
            'phone1', 'phone2', 'email', 'address', 'gender',
            'educational_qualification', 'university_college',
            'percentage', 'year_of_passing', 'heard_from',
            'course_interested_input', 'flexible_timings'
        ]
        extra_kwargs = {f: {'required': False} for f in fields}

    def to_internal_value(self, data):
        data = data.copy()
        raw_course = data.pop('course_interested_input', None)

        if raw_course is not None:
            raw_course = str(raw_course).strip()
            if raw_course == '':
                data['course_interested'] = None
            elif raw_course.isdigit():
                try:
                    data['course_interested'] = course.objects.get(pk=int(raw_course))
                except course.DoesNotExist:
                    raise serializers.ValidationError({
                        'course_interested_input': f'Course with ID {raw_course} not found.'
                    })
            else:
                try:
                    data['course_interested'] = course.objects.get(course_name__iexact=raw_course)
                except course.DoesNotExist:
                    raise serializers.ValidationError({
                        'course_interested_input': f'Course "{raw_course}" not found.'
                    })

        return super().to_internal_value(data)


# class FollowUpDetailSerializer(serializers.ModelSerializer):
#     enquiry = EnquiryNestedUpdateSerializer(write_only=True)
#     enquiry_data = serializers.SerializerMethodField(read_only=True)

#     class Meta:
#         model = FollowUps
#         fields = [
#             'id',
#             'enquiry',
#             'enquiry_data',
#             'followup_date',
#             'status',
#             'remarks',
#             'next_followup_date',
#         ]
#         read_only_fields = ('followup_date', 'enquiry_data')

#     def get_enquiry_data(self, obj):
#         # RELOAD the enquiry from DB to get latest saved values
#         enquiry = Enquiry.objects.select_related('course_interested').get(pk=obj.enquiry.pk)
#         return {
#             "student_name": enquiry.student_name,
#             "date_of_birth": str(enquiry.date_of_birth) if enquiry.date_of_birth else None,
#             "guardian_name": enquiry.guardian_name,
#             "occupation": enquiry.occupation,
#             "phone1": enquiry.phone1,
#             "phone2": enquiry.phone2,
#             "email": enquiry.email,
#             "address": enquiry.address,
#             "gender": enquiry.gender,
#             "educational_qualification": enquiry.educational_qualification,
#             "university_college": enquiry.university_college,
#             "percentage": enquiry.percentage,
#             "year_of_passing": enquiry.year_of_passing,
#             "heard_from": enquiry.heard_from,
#             "course_interested": enquiry.course_interested.course_name if enquiry.course_interested else None,
#             "flexible_timings": enquiry.flexible_timings,
#             "enquiry_date": str(enquiry.enquiry_date)
#         }

#     def update(self, instance, validated_data):
#         enquiry_data = validated_data.pop('enquiry', {})

#         # Update FollowUp fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Update Enquiry if provided
#         if enquiry_data:
#             enquiry = instance.enquiry
#             enquiry_serializer = EnquiryNestedUpdateSerializer(
#                 enquiry, data=enquiry_data, partial=True
#             )
#             enquiry_serializer.is_valid(raise_exception=True)
#             enquiry_serializer.save()  # This saves to DB

#         return instance


# serializers.py
from rest_framework import serializers
from .models import FollowUps, Enquiry, FollowUpRemark, course

class FollowUpRemarkSerializer(serializers.ModelSerializer):
    added_on = serializers.DateTimeField(format='%d/%m/%Y, %I:%M %p', read_only=True)

    class Meta:
        model = FollowUpRemark
        fields = ['id', 'content', 'added_on']
        read_only_fields = ['id', 'added_on']


class FollowUpDetailSerializer(serializers.ModelSerializer):
    enquiry = EnquiryNestedUpdateSerializer(write_only=True)
    
    # This field uses get_enquiry_data()
    enquiry_data = serializers.SerializerMethodField()
    
    # Accept list of remarks
    remarks = serializers.ListField(
        child=serializers.CharField(max_length=1000, allow_blank=True),
        write_only=True,
        required=False
    )
    
    # Show all remarks history
    remarks_history = FollowUpRemarkSerializer(many=True, read_only=True, source='remarks')

    class Meta:
        model = FollowUps
        fields = [
            'id', 'followup_date', 'status', 'next_followup_date',
            'enquiry', 'enquiry_data', 'remarks', 'remarks_history'
        ]
        read_only_fields = ('followup_date', 'enquiry_data', 'remarks_history')

    # THIS METHOD WAS MISSING → ADD IT!
    def get_enquiry_data(self, obj):
        e = Enquiry.objects.select_related('course_interested').get(pk=obj.enquiry.pk)
        return {
            "student_name": e.student_name,
            "date_of_birth": str(e.date_of_birth) if e.date_of_birth else None,
            "guardian_name": e.guardian_name,
            "occupation": e.occupation,
            "phone1": e.phone1,
            "phone2": e.phone2,
            "email": e.email,
            "address": e.address,
            "gender": e.gender,
            "educational_qualification": e.educational_qualification,
            "university_college": e.university_college,
            "percentage": e.percentage,
            "year_of_passing": e.year_of_passing,
            "heard_from": e.heard_from,
            "course_interested": e.course_interested.course_name if e.course_interested else None,
            "flexible_timings": e.flexible_timings,
            "enquiry_date": str(e.enquiry_date)
        }

    def update(self, instance, validated_data):
        enquiry_data = validated_data.pop('enquiry', {})
        new_remarks = validated_data.pop('remarks', [])

        # Update FollowUp fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Enquiry
        if enquiry_data:
            enquiry = instance.enquiry
            serializer = EnquiryNestedUpdateSerializer(enquiry, data=enquiry_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        # Add remarks
        for content in new_remarks:
            content = content.strip()
            if content:
                FollowUpRemark.objects.create(followup=instance, content=content)

        return instance