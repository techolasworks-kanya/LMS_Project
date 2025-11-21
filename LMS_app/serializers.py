from rest_framework import serializers
from .models import *


class LocalDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        if not value:
            return None
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_default_timezone())
        value = timezone.localtime(value)
        return super().to_representation(value)

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
    course_name = serializers.CharField(
        source='course_interested.course_name',
        read_only=True
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
        raw_course = data.get('course_interested')

        if isinstance(raw_course, list):
            raw_course = raw_course[0]
        raw_course = str(raw_course or '').strip().strip('"\'')
        course_obj = None

        if raw_course:
            if raw_course.isdigit():
                course_obj = course.objects.filter(pk=int(raw_course)).first()
            if not course_obj:
                course_obj = course.objects.filter(course_name__iexact=raw_course).first()
            if not course_obj:
                course_obj = course.objects.filter(course_name__icontains=raw_course).first()
            if not course_obj:
                available = list(course.objects.values_list('course_name', flat=True))
                raise serializers.ValidationError({
                    "course_interested": f'Course "{raw_course}" not found. Available: {available}'
                })
            data['course_interested'] = course_obj
        else:
            data['course_interested'] = None

        # === Date of birth ===
        raw_dob = data.get('date_of_birth')
        if raw_dob:
            if isinstance(raw_dob, list):
                raw_dob = raw_dob[0]
            raw_dob = str(raw_dob).strip()
            if raw_dob.lower() not in ['', 'null', 'undefined']:
                parsed = None
                for fmt in ('%d-%m-%Y', '%Y-%m-%d'):
                    try:
                        parsed = datetime.strptime(raw_dob, fmt).date()
                        break
                    except ValueError:
                        continue
                if not parsed:
                    raise serializers.ValidationError({
                        "date_of_birth": "Use dd-mm-yyyy or yyyy-mm-dd format."
                    })
                data['date_of_birth'] = parsed
            else:
                data['date_of_birth'] = None

        # Clean blank/null fields
        empty_vals = ['', 'null', 'undefined', 'None']
        for f in [
            'guardian_name', 'occupation', 'phone2', 'email', 'address',
            'gender', 'university_college', 'percentage', 'year_of_passing',
            'flexible_timings'
        ]:
            v = data.get(f)
            if isinstance(v, list):
                v = v[0]
            data[f] = None if str(v).strip() in empty_vals else v

        return data
    
class EnquiryListSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(
        source='course_interested.course_name',
        read_only=True,
        allow_null=True
    )
    enquiry_date = serializers.SerializerMethodField()

    class Meta:
        model = Enquiry
        fields = [
            'id', 'student_name', 'enquiry_date',
            'course_name', 'heard_from'
        ]

    def get_enquiry_date(self, obj):
        if obj.enquiry_date:
            return obj.enquiry_date.strftime('%d-%m-%Y')
        return None

    
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
    


class FollowUpRemarkSerializer(serializers.ModelSerializer):
    added_on = LocalDateTimeField(format='%d/%m/%Y, %I:%M %p', read_only=True)

    class Meta:
        model = FollowUpRemark
        fields = ['id', 'content', 'added_on']
        read_only_fields = ['id', 'added_on']



class FollowUpListSerializer(serializers.ModelSerializer):
    followup_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
    next_followup_date = serializers.DateField(format='%d-%m-%Y', allow_null=True, read_only=True)
    enquiry_data = serializers.SerializerMethodField()
    latest_remark = FollowUpRemarkSerializer(source='remarks.first', read_only=True)

    class Meta:
        model = FollowUps
        fields = [
            'id', 'followup_date', 'status', 'next_followup_date',
            'enquiry_data', 'latest_remark',
        ]

    def get_enquiry_data(self, obj):
        e = Enquiry.objects.select_related('course_interested').get(pk=obj.enquiry.pk)
        return {
            "student_name": e.student_name,
            "date_of_birth": e.date_of_birth.strftime('%d-%m-%Y') if e.date_of_birth else None,
            "guardian_name": e.guardian_name,
            "phone1": e.phone1,
            "course_interested": e.course_interested.course_name if e.course_interested else None,
            "enquiry_date": e.enquiry_date.strftime('%d-%m-%Y')
        }

    # def get_latest_remark(self, obj):
    #     remark = obj.remarks.first()
    #     if remark:
    #         return {
    #             "content": remark.content,
    #             "added_on": remark.added_on.strftime('%d/%m/%Y, %I:%M %p')
    #         }
    #     return None
# serializers.py
class EnquiryNestedUpdateSerializer(serializers.ModelSerializer):
    course_interested = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
   

    class Meta:
        model = Enquiry
        fields = [
            'student_name', 'date_of_birth', 'guardian_name', 'occupation',
            'phone1', 'phone2', 'email', 'address', 'gender',
            'educational_qualification', 'university_college',
            'percentage', 'year_of_passing', 'heard_from',
            'flexible_timings', 'course_interested'
        ]
    def update(self, instance, validated_data):
        raw_course_name = validated_data.pop('course_interested', None)
        if raw_course_name is not None:
            raw_course_name = raw_course_name.strip()
            if raw_course_name:
                # Find or create course
                course_obj, _ = course.objects.get_or_create(course_name=raw_course_name)
                validated_data['course_interested'] = course_obj
            else:
                validated_data['course_interested'] = None

        return super().update(instance, validated_data)

    

# serializers.py

 
from datetime import datetime, date

class FollowUpDetailSerializer(serializers.ModelSerializer):
    # WRITE-ONLY INPUT FIELDS
    remarks = serializers.ListField(
        child=serializers.CharField(max_length=1000, allow_blank=True),
        write_only=True,
        required=False
    )
    enquiry_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="List of enquiry IDs to convert to follow-ups"
    )
    enquiry = EnquiryNestedUpdateSerializer(write_only=True, required=False)

    # READ-ONLY OUTPUT
    followup_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
    next_followup_date = serializers.DateField(
        format='%d-%m-%Y',
        input_formats=['%d-%m-%Y', '%Y-%m-%d'],  # Fixed: Accept both formats
        allow_null=True,
        required=False
    )
    enquiry_data = serializers.SerializerMethodField()
    remarks_history = FollowUpRemarkSerializer(many=True, read_only=True, source='remarks')

    class Meta:
        model = FollowUps
        fields = [
            'id', 'followup_date', 'status', 'next_followup_date',
            'enquiry_data', 'remarks_history',
            'enquiry_ids', 'remarks', 'enquiry'
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

   
    def update(self, instance, validated_data):
    # === ENQUIRY ===
        enquiry_data = validated_data.pop('enquiry', None)
        if enquiry_data:
            enquiry_serializer = EnquiryNestedUpdateSerializer(
                instance.enquiry, data=enquiry_data, partial=True
            )
            enquiry_serializer.is_valid(raise_exception=True)
            enquiry_serializer.save()

        # === REMARKS ===
        remarks = validated_data.pop('remarks', [])
        for content in remarks:
            if content.strip():
                FollowUpRemark.objects.create(followup=instance, content=content.strip())

        # === UPDATE FOLLOWUP FIELDS ===
        return super().update(instance, validated_data)



#Admission Serializer

class AdmissionListSerializer(serializers.ModelSerializer):
    # ----- Safe fields that come from Enquiry (can be None) -----
    student_name       = serializers.SerializerMethodField()
    date_of_birth      = serializers.SerializerMethodField()
    course_name        = serializers.SerializerMethodField()
    qualification      = serializers.SerializerMethodField()
    phone1             = serializers.SerializerMethodField()
    phone2             = serializers.SerializerMethodField()
    email              = serializers.SerializerMethodField()
    address            = serializers.SerializerMethodField()
    gender             = serializers.SerializerMethodField()
    percentage         = serializers.SerializerMethodField()
    year_of_passing    = serializers.SerializerMethodField()
    enquiry_date       = serializers.SerializerMethodField()
    university         = serializers.SerializerMethodField()
    flexible_timings   = serializers.SerializerMethodField()

    enquiry_source      = serializers.SerializerMethodField()
    guardian_name      = serializers.SerializerMethodField()
    guardian_occupation = serializers.SerializerMethodField()


    # ADD THESE NEW FIELDS HERE
    student_photo = serializers.ImageField(read_only=True)
    aadhaar_number = serializers.CharField(read_only=True)
    educational_certificate = serializers.FileField(read_only=True)
    class_schedule = serializers.CharField(read_only=True)
    class_timing = serializers.CharField(read_only=True)
    payment_structure = serializers.CharField(read_only=True)
    nactit_interest = serializers.CharField(source='get_interested_in_nactit_display')
    nactit_fee = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = Admission
        fields = [
            'id', 'admission_date', 'status', 'fee_paid',
            'student_name', 'date_of_birth', 'course_name', 'qualification',
            'phone1', 'phone2', 'email', 'address', 'gender',
            'percentage', 'year_of_passing', 'enquiry_date',
            'enquiry_source', 'guardian_name', 'guardian_occupation',
            'university', 'flexible_timings',
#------------------- New Fields -------------------
            'student_photo', 'aadhaar_number', 'educational_certificate',
            'class_schedule', 'class_timing', 'payment_structure','nactit_interest','nactit_fee'
        ]

    # ------------------- Safe getters -------------------
    def get_student_name(self, obj):
        return obj.enquiry.student_name if obj.enquiry else None

    def get_date_of_birth(self, obj):
        return obj.enquiry.date_of_birth if obj.enquiry else None

    def get_course_name(self, obj):
        if obj.enquiry and obj.enquiry.course_interested:
            return obj.enquiry.course_interested.course_name
        return None

    def get_qualification(self, obj):
        return obj.enquiry.educational_qualification if obj.enquiry else None

    def get_phone1(self, obj):
        return obj.enquiry.phone1 if obj.enquiry else None

    def get_phone2(self, obj):
        return obj.enquiry.phone2 if obj.enquiry else None

    def get_email(self, obj):
        return obj.enquiry.email if obj.enquiry else None

    def get_address(self, obj):
        return obj.enquiry.address if obj.enquiry else None

    def get_gender(self, obj):
        return obj.enquiry.gender if obj.enquiry else None

    def get_percentage(self, obj):
        return obj.enquiry.percentage if obj.enquiry else None

    def get_year_of_passing(self, obj):
        return obj.enquiry.year_of_passing if obj.enquiry else None

    def get_enquiry_date(self, obj):
        if obj.enquiry and obj.enquiry.enquiry_date:
            return obj.enquiry.enquiry_date.strftime('%d-%m-%Y')
        return None

    def get_university(self, obj):
        return obj.enquiry.university_college if obj.enquiry else None

    def get_flexible_timings(self, obj):
        return obj.enquiry.flexible_timings if obj.enquiry else None

 
    def get_enquiry_source(self, obj):
        if obj.enquiry and obj.enquiry.heard_from:
            return obj.enquiry.get_heard_from_display()  
        return "Unknown"

   
    def get_guardian_name(self, obj):
        return obj.enquiry.guardian_name if obj.enquiry and obj.enquiry.guardian_name else "—"

   
    def get_guardian_occupation(self, obj):
        if not obj.enquiry:
            return "—"
        latest_followup = obj.enquiry.follow_up_actions.order_by('-followup_date').first()
        if latest_followup and latest_followup.guardian_occupation:
            return latest_followup.guardian_occupation
        return obj.enquiry.occupation or "—"

class AdmissionCreateSerializer(serializers.ModelSerializer):
    enquiry_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of enquiry IDs to convert to admissions"
    )

    followup_ids = serializers.ListField(          # <--- ADD THIS
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of followup IDs to convert to admissions"
    )

    def validate(self, attrs):
        # Must provide either enquiry_ids or followup_id
        if not attrs.get("enquiry_ids") and not attrs.get("followup_ids"):
            raise serializers.ValidationError(
                "Either 'enquiry_ids' or 'followup_id' is required."
            )

        return attrs
    
    class Meta:
        model = Admission
        fields = ['enquiry_ids','followup_ids']
   
from django.shortcuts import get_object_or_404
class AdmissionUpdateSerializer(serializers.ModelSerializer):
    enquiry_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    student_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    guardian_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone1 = serializers.CharField(max_length=15)
    phone2 = serializers.CharField(max_length=15, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'], required=False)
    educational_qualification = serializers.CharField(max_length=200, required=False)
    university_college = serializers.CharField(max_length=200, required=False, allow_blank=True)
    percentage = serializers.FloatField(required=False, allow_null=True)
    year_of_passing = serializers.IntegerField(required=False, allow_null=True)
    course_interested = serializers.PrimaryKeyRelatedField(
        queryset=course.objects.all(), required=True
    )

    class Meta:
        model = Admission
        fields = [
            # Core
            'id', 'enquiry_id',
            'student_name', 'date_of_birth', 'guardian_name',
            'phone1', 'phone2', 'email', 'address', 'gender',
            'educational_qualification', 'university_college',
            'percentage', 'year_of_passing', 'course_interested',
            'student_photo', 'aadhaar_number', 'educational_certificate',
            'class_schedule', 'class_timing', 'payment_structure',
            'interested_in_nactit', 'status', 'fee_paid'
        ]

    def create(self, validated_data):
        enquiry_id = validated_data.pop('enquiry_id', None)
        course_interested = validated_data.pop('course_interested')

        # Create Enquiry if manual
        if not enquiry_id:
            enquiry = Enquiry.objects.create(
                student_name=validated_data.pop('student_name'),
                date_of_birth=validated_data.pop('date_of_birth', None),
                guardian_name=validated_data.pop('guardian_name', ''),
                phone1=validated_data.pop('phone1'),
                phone2=validated_data.pop('phone2', ''),
                email=validated_data.pop('email', ''),
                address=validated_data.pop('address', ''),
                gender=validated_data.pop('gender', 'other'),
                educational_qualification=validated_data.pop('educational_qualification', ''),
                university_college=validated_data.pop('university_college', ''),
                percentage=validated_data.pop('percentage', None),
                year_of_passing=validated_data.pop('year_of_passing', None),
                course_interested=course_interested,
            )
        else:
            enquiry = get_object_or_404(Enquiry, id=enquiry_id)

        # Create Admission
        admission = Admission.objects.create(
            enquiry=enquiry,
            course=course_interested,
            status=validated_data.get('status', 'pending'),
            **validated_data
        )

        # Auto NACTIT fee
        if admission.interested_in_nactit == 'yes':
            admission.nactit_fee = 1000.00
            admission.save()

        return admission

    def update(self, instance, validated_data):
        # Same logic as before — update enquiry + admission
        enquiry = instance.enquiry
        if enquiry:
            for attr, value in validated_data.items():
                if attr in ['student_name', 'phone1', 'email', 'course_interested', 'guardian_name', 'date_of_birth', 'address', 'gender', 'educational_qualification', 'university_college', 'percentage', 'year_of_passing']:
                    setattr(enquiry, attr, value)
            enquiry.save()

        # Update admission fields
        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)
        if 'course_interested' in validated_data:
            instance.course = validated_data['course_interested']

        # NACTIT fee logic
        if instance.interested_in_nactit == 'yes':
            instance.nactit_fee = 1000.00
        else:
            instance.nactit_fee = 0.00

        instance.save()
        return instance



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



#notfication APIs
class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%d-%m-%Y %I:%M %p', read_only=True)
    module_display = serializers.CharField(source='get_module_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'module', 'module_display', 'content',
            'created_at', 'is_read'
        ]
        read_only_fields = ['created_at', 'is_read', 'module_display']

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['module', 'content']  # Only accept these

    def create(self, validated_data):
       
        return Notification.objects.create(
            module=validated_data['module'],
            content=validated_data['content'],
            is_read=False
        )
    
class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['is_read'] 
    




class ConversionStatsSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    total_enquiry = serializers.IntegerField()
    total_admission = serializers.IntegerField()
    admission_rate = serializers.CharField()



# enquiry source chart serializers
class EnquirySourceStatsSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    sources = serializers.DictField()
    top_source = serializers.CharField()
    top_source_count = serializers.IntegerField()


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['amount', 'admission_fee', 'payment_mode', 'transaction_id', 'remarks']

    def validate(self, data):
        if data['payment_mode'] == 'upi' and not data.get('transaction_id'):
            raise serializers.ValidationError("Transaction ID required for UPI")
        return data