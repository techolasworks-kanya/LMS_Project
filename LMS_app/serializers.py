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
        

from rest_framework import serializers
from .models import Enquiry, course
from datetime import datetime

class EnquiryCreateSerializer(serializers.ModelSerializer):
    # INPUT: Accept raw string or ID
    course_interested_input = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Enter course name or ID"
    )

    # OUTPUT: Show course name
    course_interested = serializers.CharField(
        source='course_interested.course_name',
        read_only=True,
        allow_null=True
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

    def to_internal_value(self, data):
        data = dict(data)
        raw_dob = data.get('date_of_birth')
        if raw_dob:
            if isinstance(raw_dob, list):
                raw_dob = raw_dob[0] if raw_dob else ''
            raw_dob = str(raw_dob).strip()

            if raw_dob in ['', 'null', 'undefined']:
                data['date_of_birth'] = None
            else:
                # Try dd-mm-yyyy first
                parsed = None
                for fmt in ('%d-%m-%Y', '%Y-%m-%d'):
                    try:
                        parsed = datetime.strptime(raw_dob, fmt).date()
                        break
                    except ValueError:
                        continue
                if parsed:
                    data['date_of_birth'] = parsed
                else:
                    raise serializers.ValidationError({
                        'date_of_birth': 'Invalid date format. Use dd-mm-yyyy or yyyy-mm-dd.'
                    })

        raw_course = data.get('course_interested_input')

        if raw_course is not None:
            # Handle list from form-data
            if isinstance(raw_course, list):
                raw_course = raw_course[0].strip() if raw_course else ''
            else:
                raw_course = str(raw_course).strip()

            if raw_course:
                # Try ID first
                if raw_course.isdigit():
                    try:
                        course_obj = course.objects.get(id=int(raw_course))
                        data['course_interested'] = course_obj
                        # Save raw input for _course_input
                        data['_course_input'] = raw_course
                        data.pop('course_interested_input', None)
                        return super().to_internal_value(data)
                    except (course.DoesNotExist, ValueError):
                        pass

                # Try name
                try:
                    course_obj = course.objects.get(course_name__iexact=raw_course)
                    data['course_interested'] = course_obj
                    data['_course_input'] = raw_course
                except course.DoesNotExist:
                    raise serializers.ValidationError({
                        'course_interested_input': f'Course "{raw_course}" not found.'
                    })
            else:
                data['course_interested'] = None
                data['_course_input'] = None

            data.pop('course_interested_input', None)

        # Clean empty fields
        for field in ['date_of_birth', 'guardian_name', 'occupation', 'phone2',
                      'email', 'address', 'gender', 'university_college',
                      'percentage', 'year_of_passing', 'flexible_timings']:
            val = data.get(field)
            if isinstance(val, list):
                val = val[0] if val else ''
            if str(val).strip() in ['', 'null', 'undefined']:
                data[field] = None

        return super().to_internal_value(data)


class EnquiryListSerializer(serializers.ModelSerializer):
    course_interested = serializers.CharField(
        source='course_interested.course_name',
        read_only=True,
        allow_null=True
    )
    course_interested_input = serializers.SerializerMethodField()
    enquiry_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
    date_of_birth = serializers.DateField(format='%d-%m-%Y', read_only=True, allow_null=True)

    class Meta:
        model = Enquiry
        fields = [
            'id', 'student_name', 'enquiry_date',
            'course_interested', 'course_interested_input', 'heard_from','date_of_birth'
        ]

    def get_course_interested_input(self, obj):
        return getattr(obj, '_course_input', None)



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
    




# class FollowUpListSerializer(serializers.ModelSerializer):
#     enquiry_data = serializers.SerializerMethodField()
#     followup_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
#     latest_remark = serializers.SerializerMethodField()
#     next_followup_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
#     status = serializers.CharField()
#     id = serializers.IntegerField()

#     class Meta:
#         model = FollowUps
#         fields = [
#             'id',
#             'followup_date',
#             'status',
#             'next_followup_date',
#             'enquiry_data',
#             'latest_remark'
#         ]

#     def get_enquiry_data(self, obj):
#         e = obj.enquiry
#         return {
#             "student_name": e.student_name,
#             "phone1": e.phone1,
#             "course_interested": e.course_interested.course_name if e.course_interested else None,
#             "heard_from": e.heard_from,
#         }

#     def get_latest_remark(self, obj):
#         remark = obj.remarks.first()  # Most recent (ordered by -added_on)
#         if remark:
#             return {
#                 "content": remark.content,
#                 "added_on": remark.added_on.strftime('%d/%m/%Y, %I:%M %p')
#             }
#         return None
class FollowUpListSerializer(serializers.ModelSerializer):
    followup_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
    next_followup_date = serializers.DateField(format='%d-%m-%Y', allow_null=True, read_only=True)
    enquiry_data = serializers.SerializerMethodField()
    latest_remark = serializers.SerializerMethodField()

    class Meta:
        model = FollowUps
        fields = [
            'id', 'followup_date', 'status', 'next_followup_date',
            'enquiry_data', 'latest_remark'
        ]

    def get_enquiry_data(self, obj):
        e = obj.enquiry
        return {
            "student_name": e.student_name,
            "date_of_birth": e.date_of_birth.strftime('%d-%m-%Y') if e.date_of_birth else None,
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
            "enquiry_date": e.enquiry_date.strftime('%d-%m-%Y'),
            "flexible_timings": e.flexible_timings
        }

    def get_latest_remark(self, obj):
        remark = obj.remarks.first()
        if remark:
            return {
                "content": remark.content,
                "added_on": remark.added_on.strftime('%d/%m/%Y, %I:%M %p')
            }
        return None

# serializers.py
class EnquiryNestedUpdateSerializer(serializers.ModelSerializer):
    course_interested_input = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Course name (e.g. 'Python') or ID (e.g. 5)"
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

    def to_internal_value(self, data):
        data = data.copy()
        raw = data.pop('course_interested_input', None)
        if raw is not None:
            raw = str(raw).strip()
            if raw == '':
                data['course_interested'] = None
            elif raw.isdigit():
                try:
                    data['course_interested'] = course.objects.get(id=int(raw))
                except course.DoesNotExist:
                    raise serializers.ValidationError({
                        'course_interested_input': f'Course ID {raw} not found.'
                    })
            else:
                try:
                    data['course_interested'] = course.objects.get(course_name__iexact=raw)
                except course.DoesNotExist:
                    raise serializers.ValidationError({
                        'course_interested_input': f'Course "{raw}" not found.'
                    })
        return super().to_internal_value(data)




# serializers.py
class FollowUpRemarkSerializer(serializers.ModelSerializer):
    added_on = serializers.DateTimeField(format='%d/%m/%Y, %I:%M %p', read_only=True)

    class Meta:
        model = FollowUpRemark
        fields = ['id', 'content', 'added_on']
        read_only_fields = ['id', 'added_on']




# class FollowUpDetailSerializer(serializers.ModelSerializer):
#     enquiry = EnquiryNestedUpdateSerializer()  # ← writable nested
#     followup_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
#     next_followup_date = serializers.DateField(format='%d-%m-%Y', allow_null=True, read_only=True)
#     remarks = serializers.ListField(
#         child=serializers.CharField(max_length=1000, allow_blank=True),
#         write_only=True,
#         required=False
#     )
#     enquiry_data = serializers.SerializerMethodField()
#     remarks_history = FollowUpRemarkSerializer(many=True, read_only=True, source='remarks')

#     class Meta:
#         model = FollowUps
#         fields = [
#             'id', 'followup_date', 'status', 'next_followup_date',
#             'enquiry', 'enquiry_data', 'remarks', 'remarks_history'
#         ]
#         read_only_fields = ('id', 'followup_date', 'enquiry_data', 'remarks_history')

#     def get_enquiry_data(self, obj):
#         e = obj.enquiry
#         return {
#             "student_name": e.student_name,
#             "phone1": e.phone1,
#             "course_interested": e.course_interested.course_name if e.course_interested else None,
#             "heard_from": e.heard_from,
#             "enquiry_date": str(e.enquiry_date),
#             "date_of_birth": e.date_of_birth.strftime('%d-%m-%Y') if e.date_of_birth else None,
#         }

#     # === FIXED: Custom update() for nested fields ===
#     def update(self, instance, validated_data):
#         # 1. Update FollowUp fields
#         instance.status = validated_data.get('status', instance.status)
#         instance.next_followup_date = validated_data.get('next_followup_date', instance.next_followup_date)
#         instance.save()

#         # 2. Update nested Enquiry
#         enquiry_data = validated_data.pop('enquiry', {})
#         if enquiry_data:
#             enquiry = instance.enquiry
#             enquiry_serializer = EnquiryNestedUpdateSerializer(enquiry, data=enquiry_data, partial=True)
#             enquiry_serializer.is_valid(raise_exception=True)
#             enquiry_serializer.save()

#         # 3. Add new remarks
#         remarks = validated_data.pop('remarks', [])
#         for content in remarks:
#             if content.strip():
#                 FollowUpRemark.objects.create(followup=instance, content=content.strip())

#         return instance
# class FollowUpDetailSerializer(serializers.ModelSerializer):
#     # ACCEPT LIST OF IDs
#     enquiry_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         write_only=True,
#         required=True,
#         help_text="List of enquiry IDs to convert to follow-ups"
#     )

#     remarks = serializers.ListField(
#         child=serializers.CharField(max_length=1000, allow_blank=True),
#         write_only=True,
#         required=False
#     )

#     enquiry_data = serializers.SerializerMethodField()
#     remarks_history = FollowUpRemarkSerializer(many=True, read_only=True, source='remarks')

#     class Meta:
#         model = FollowUps
#         fields = [
#             'enquiry_ids', 'status', 'next_followup_date',
#             'enquiry_data', 'remarks', 'remarks_history'
#         ]
#         read_only_fields = ('enquiry_data', 'remarks_history')

#     def get_enquiry_data(self, obj):
#         e = obj.enquiry
#         return {
#             "student_name": e.student_name,
#             "phone1": e.phone1,
#             "course_interested": e.course_interested.course_name if e.course_interested else None,
#             "heard_from": e.heard_from,
#             "enquiry_date": e.enquiry_date.strftime('%d-%m-%Y')
#         }   
class FollowUpDetailSerializer(serializers.ModelSerializer):
    followup_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
    next_followup_date = serializers.DateField(format='%d-%m-%Y', allow_null=True, read_only=True)
    enquiry_data = serializers.SerializerMethodField()
    remarks_history = FollowUpRemarkSerializer(many=True, read_only=True, source='remarks')

    class Meta:
        model = FollowUps
        fields = [
            'id', 'followup_date', 'status', 'next_followup_date',
            'enquiry_data', 'remarks_history'
        ]

    def get_enquiry_data(self, obj):
        e = obj.enquiry
        return {
            "student_name": e.student_name,
            "date_of_birth": e.date_of_birth.strftime('%d-%m-%Y') if e.date_of_birth else None,
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
            "enquiry_date": e.enquiry_date.strftime('%d-%m-%Y'),
            "flexible_timings": e.flexible_timings
        }
#Admission Serializer
class AdmissionListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='enquiry.student_name')
    course_name = serializers.CharField(source='enquiry.course_interested.course_name', allow_null=True)
    qualification = serializers.CharField(source='enquiry.educational_qualification')
    phone1 = serializers.CharField(source='enquiry.phone1')
    email = serializers.CharField(source='enquiry.email', allow_null=True)

    class Meta:
        model = Admission
        fields = [
            'id', 'admission_date', 'status', 'fee_paid',
            'student_name', 'course_name', 'qualification', 'phone1', 'email'
        ]

class AdmissionCreateSerializer(serializers.ModelSerializer):
    enquiry_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="List of enquiry IDs to convert to admissions"
    )

    class Meta:
        model = Admission
        fields = ['enquiry_ids']



# serializers.py
class NotInterestedLeadListSerializer(serializers.ModelSerializer):
    last_followup_date = serializers.DateField(format='%d/%m/%Y')
    student_name = serializers.CharField(source='enquiry.student_name')
    course_name = serializers.CharField(
        source='enquiry.course_interested.course_name',
        allow_null=True
    )
    qualification = serializers.CharField(source='enquiry.educational_qualification')
    phone1 = serializers.CharField(source='enquiry.phone1')
    status = serializers.ChoiceField(choices=[
        ('not_interested', 'Not Interested'),
        ('rejected', 'Rejected'),
        ('follow_up', 'Follow Up'),
    ])
    email = serializers.CharField(source='enquiry.email', allow_null=True)

    class Meta:
        model = NotInterestedLead
        fields = [
            'id',
            'last_followup_date',
            'student_name',
            'course_name',
            'qualification',
            'phone1',
            'status',
            'email'
           
        ]