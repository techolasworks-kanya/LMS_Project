from decimal import Decimal
import re
from rest_framework import serializers
from .models import *
from django.utils import timezone
from datetime import timedelta  
from datetime import datetime
import datetime as dt_module 





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
        
from rest_framework.exceptions import ValidationError  
class EnquiryCreateSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course_interested.course_name',read_only=True)

    class Meta:
        model = Enquiry
        fields = '__all__'
        extra_kwargs = {
            'student_name': {'required': True},
            'phone1': {'required': True},
            'educational_qualification': {'required': True},
            'heard_from': {'required': True},
            'course_interested': {'required': True},
        }

  
        
    
    def to_internal_value(self, data):
        data = dict(data)

        student_name = data.get('student_name', '')
        if isinstance(student_name, list):
            student_name = student_name[0] if student_name else ''
        student_name = str(student_name).strip()

        if len(student_name) > 55:
            raise serializers.ValidationError({
                "message": "Student name is too long. Maximum 55 characters allowed."
            })

        data['student_name'] = student_name

        # === Guardian name ===
        guardian_name = data.get('guardian_name', '')
        if isinstance(guardian_name, list):
            guardian_name = guardian_name[0] if guardian_name else ''
        guardian_name = str(guardian_name).strip()

        if len(guardian_name) > 40:
            raise serializers.ValidationError({
                "message": "Guardian name is too long. Maximum 40 characters allowed"
            })
        
        #=== Guardian occupation ===

        guardian_occupation = data.get('occupation', '')
        if isinstance(guardian_occupation, list):
            guardian_occupation = guardian_occupation[0] if guardian_occupation else ''
        guardian_occupation = str(guardian_occupation).strip()
        if len(guardian_occupation) < 2 and guardian_occupation != '':
            raise serializers.ValidationError({
                "message": "Guardian occupation is too short. Please provide a valid occupation."
            })
        if len(guardian_occupation) > 50:
            raise serializers.ValidationError({
                "message": "Guardian occupation is too long. Maximum 50 characters allowed."
            })

        
        
        # === Email & Phone Duplicate Check (Add this here!) ===
        phone1 = data.get('phone1')
        if isinstance(phone1, list):
            phone1 = phone1[0] if phone1 else None
        phone1 = str(phone1).strip() if phone1 else None



        email = data.get('email')
        if isinstance(email, list):
            email = email[0] if email else None
        email = str(email).strip().lower() if email else None

        if phone1 or email:
            qs = Enquiry.objects.filter(is_archived=False)

            if phone1 and qs.filter(phone1=phone1).exists():
                raise serializers.ValidationError({
                    "message": "An enquiry with this phone number already exists."
                })
            if len(phone1) < 9:
                raise serializers.ValidationError({
                    "message": "Phone number is too short. Please provide a valid phone number."
                })
            if len(phone1) > 16:
                raise serializers.ValidationError({
                    "message": "Phone number is too long. Maximum 15 characters allowed."
                })
            #no special charactors allow in the phone number field
            if phone1 and not phone1.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                raise serializers.ValidationError({
                    "message": "Please provide a valid phone number."   
                })
            data['phone1'] = phone1



           
            if email and qs.filter(email__iexact=email).exists():
                raise serializers.ValidationError({
                    "message": "An enquiry with this email already exists."
                })
            email = data.get('email')
        if isinstance(email, list):
            email = email[0] if email else None
        email = str(email).strip().lower() if email else None

        if email:
            if len(email) > 100:
                raise serializers.ValidationError({
                    "message": "Email address is too long. Maximum 100 characters allowed."
                })
            if len(email) < 5:
                raise serializers.ValidationError({
                    "message": "Email address is too short. Please provide a valid email."
                })
        else:
            email = None
        data['email'] = email
#phone2 length check
        phone2 = data.get('phone2', '')
        if isinstance(phone2, list):
            phone2 = phone2[0] if phone2 else ''
        phone2 = str(phone2).strip()
        if phone2:
            if len(phone2) < 9:
                raise serializers.ValidationError({
                    "message": "Secondary phone number is too short. Please provide a valid phone number."
                })
            if len(phone2) > 16:
                raise serializers.ValidationError({
                    "message": "Secondary phone number is too long. Maximum 15 characters allowed."
                })
            #no special charactors allow in the phone number field
            if not phone2.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                raise serializers.ValidationError({
                    "message": "Please provide a valid secondary phone number."   
                })



        #=====address minimum length check====There is no any Max character limit in the address field. and There is no any Max character limit in the address field.
        address = data.get('address', '')
        if isinstance(address, list):
            address = address[0] if address else ''
        address = str(address).strip()

        if address:
            if len(address) < 15:
                raise serializers.ValidationError({
                    "message": "Address is too short. Please provide complete address (minimum 15 characters)."
                })
            if len(address) > 300:
                raise serializers.ValidationError({
                    "message": "Address is too long. Maximum 300 characters allowed.()"
                })
        else:
            address = None

        data['address'] = address

        #====-===========qualification length check========
        qualification = data.get('educational_qualification', '')
        if isinstance(qualification, list):
            qualification = qualification[0] if qualification else ''
        qualification = str(qualification).strip()

        if not qualification:
            raise serializers.ValidationError({
                "message": "Educational qualification is required."
            })

        qual_len = len(qualification)

        if qual_len < 3:
            raise serializers.ValidationError({
                "message": "Educational qualification is too short. Please enter full qualification. Minimum 3 characters."
            })

        if qual_len > 100:
            raise serializers.ValidationError({
                "message": "Educational qualification is too long. Maximum 100 characters allowed."
            })

        data['educational_qualification'] = qualification

        #=====university/college length check========
        university = data.get('university_college', '')
        if isinstance(university, list):
            university = university[0] if university else ''
        university = str(university).strip()
        if university:
            if len(university) < 3:
                raise serializers.ValidationError({
                    "message": "University/College name is too short. Please enter full name. Minimum 3 characters."
                })
            if len(university) > 200:
                raise serializers.ValidationError({
                    "message": "University/College name is too long. Maximum 200 characters allowed."
                })
            else:
                university = None

        year_of_passing = data.get('year_of_passing', '')

        if isinstance(year_of_passing, list):
            year_of_passing = year_of_passing[0] if year_of_passing else ''
        year_of_passing = str(year_of_passing).strip()

        if year_of_passing:
            if len(year_of_passing) != 4:
                raise serializers.ValidationError({
                    "message": "Year of passing must be a 4-digit year (e.g., 2024)."
                })

        if year_of_passing:
            if not year_of_passing.isdigit():
                raise serializers.ValidationError({
                    "message": "Year of passing must be a valid year (e.g., 2024)."
                })
            year_int = int(year_of_passing)
            current_year = dt_module.datetime.now().year

         
            if year_int > current_year:
                raise serializers.ValidationError({
                    "message": f"Year of passing must be a valid year. "
                })

            if year_int < 1930:
                raise serializers.ValidationError({
                    "message": "Year of passing must be 1930 or later."
                })

            data['year_of_passing'] = year_int
        else:
            data['year_of_passing'] = None

        # === Percentage ===
        percentage = data.get('percentage', '')
        if isinstance(percentage, list):
            percentage = percentage[0] if percentage else ''
        percentage = str(percentage).strip()
        if percentage:
            try:
                perc_float = float(percentage)
                if perc_float < 0 or perc_float > 100:
                    raise serializers.ValidationError({
                        "message": "Percentage must be between 0 and 100."
                    })
                data['percentage'] = Decimal(str(perc_float))
            except ValueError:
                raise serializers.ValidationError({
                    "message": "Percentage must be a valid number."
                })

    
        # === Course interested ===
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

   
class TodaysEnequirySerializer(serializers.ModelSerializer):
    enquiry_date = serializers.DateField(format='%d-%m-%Y', read_only=True)
    course_name = serializers.CharField(
        source='course_interested.course_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Enquiry
        fields = [
            'id', 'student_name', 'enquiry_date',
            'course_name', 'heard_from'
        ]

#Admission Serializer



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
    



class EnquiryNestedUpdateSerializer(serializers.ModelSerializer):
    course_interested = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    email = serializers.CharField(max_length=150,allow_blank=True,required=False,)
    

   

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
                course_obj, _ = course.objects.get_or_create(course_name=raw_course_name)
                validated_data['course_interested'] = course_obj
            else:
                validated_data['course_interested'] = None
       

        return super().update(instance, validated_data)
    
    # def validate(self, data):
      
    #     email = data.get('email')

    #     if email:  # Only validate if email is provided and not empty after strip
    #         email = email.strip()
    #         if len(email) < 5:
    #             raise serializers.ValidationError({
    #                 "message": "Email address is too short. Please provide a valid email."
    #             })
    #         if len(email) > 150:
    #             raise serializers.ValidationError({
    #                 "message": "Email address is too long. Maximum 150 characters allowed."
    #             })
    #         if not re.match(r"^[\w\.\+\-']+@[\w\-\.]+\.[a-zA-Z]{2,}$", email):
    #             raise serializers.ValidationError({
    #                 "message": "Please enter a valid email address (e.g. name@example.com)."
    #             })


    #         data['email'] = email

    #     return data
    

class FollowUpDetailSerializer(serializers.ModelSerializer):
    # WRITE-ONLY INPUT FIELDS
    remarks = serializers.ListField(
        child=serializers.CharField(max_length=1000, allow_blank=True),
        write_only=True,
        required=False
    )
    enquiry_ids = serializers.ListField(child=serializers.IntegerField(),write_only=True,required=True,help_text="List of enquiry IDs to convert to follow-ups")
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



class AdmissionListSerializer(serializers.ModelSerializer):
    # ----- Safe fields that come from Enquiry (can be None) -----
    student_name       = serializers.SerializerMethodField()
    date_of_birth      = serializers.SerializerMethodField()
    course_name        = serializers.SerializerMethodField()
    course_fee         = serializers.SerializerMethodField()
    qualification      = serializers.SerializerMethodField()
    phone1             = serializers.SerializerMethodField()
    phone2             = serializers.SerializerMethodField()
    email              = serializers.SerializerMethodField()
    address            = serializers.SerializerMethodField()
    gender             = serializers.SerializerMethodField()
    percentage         = serializers.SerializerMethodField()
    year_of_passing    = serializers.SerializerMethodField()
    enquiry_date       = serializers.SerializerMethodField()
    admission_date     = serializers.SerializerMethodField()
    university         = serializers.SerializerMethodField()
    flexible_timings   = serializers.SerializerMethodField()
    enquiry_source      = serializers.SerializerMethodField()
    guardian_name      = serializers.SerializerMethodField()
    guardian_occupation = serializers.SerializerMethodField()
    status  = serializers.SerializerMethodField()
    aadhaar_number = serializers.CharField(read_only=True)
    
    student_photo = serializers.SerializerMethodField()
    educational_certificate = serializers.SerializerMethodField()
    aadhaar_copy = serializers.SerializerMethodField()
    class_timing = serializers.CharField(read_only=True)
    interested_in_nactet = serializers.CharField(source='get_interested_in_nactet_display')
    nactet_fee = serializers.DecimalField(max_digits=8, decimal_places=2)
    admission_fee = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = Admission
        fields = [
            'id', 'admission_date', 'status',
            'student_name', 'date_of_birth', 'course_name','course_fee', 'qualification',
            'phone1', 'phone2', 'email', 'address', 'gender',
            'percentage', 'year_of_passing', 'enquiry_date',
            'enquiry_source', 'guardian_name', 'guardian_occupation',
            'university', 'flexible_timings',''
#------------------- New Fields -------------------
            'student_photo', 'aadhaar_number', 'educational_certificate',
             'class_timing',
            #    'payment_structure',
               'interested_in_nactet','nactet_fee','admission_fee','aadhaar_copy',
            #  'class_schedule'
        ]

    def get_student_photo(self, obj):
        if obj.student_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.student_photo.url)
            return obj.student_photo.url
        return None

    def get_educational_certificate(self, obj):
        if obj.educational_certificate:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.educational_certificate.url)
            return obj.educational_certificate.url
        return None
    
    def get_aadhaar_copy(self, obj):
        if obj.aadhaar_copy:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.aadhaar_copy.url)
            return obj.aadhaar_copy.url
        return None
    
    
    # ------------------- Safe getters -------------------
    def get_student_name(self, obj):
        return obj.enquiry.student_name if obj.enquiry else None

    def get_date_of_birth(self, obj):
        if obj.enquiry and obj.enquiry.date_of_birth:
            return obj.enquiry.date_of_birth.strftime('%Y-%m-%d')  # Changed to dd-mm-yyyy
        return None
    
    def get_admission_date(self, obj):
        return obj.admission_date.strftime('%d-%m-%Y')



    def get_course_name(self, obj):
        if obj.course:
            return obj.course.course_name
        if obj.enquiry and obj.enquiry.course_interested:
            return obj.enquiry.course_interested.course_name
        return "Not Selected"
    
    def get_course_fee(self, obj):
        if obj.course and obj.course.course_fee is not None:
            return obj.course.course_fee
        if obj.enquiry and obj.enquiry.course_interested and obj.enquiry.course_interested.course_fee is not None:
            return obj.enquiry.course_interested.course_fee
        return 0.00

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
    
    def get_status(self, obj):
        return obj.get_status_display()

 
    def get_enquiry_source(self, obj):
        if obj.enquiry and obj.enquiry.heard_from:
            return obj.enquiry.get_heard_from_display()  
        return "Unknown"

   
    def get_guardian_name(self, obj):
        return obj.enquiry.guardian_name if obj.enquiry and obj.enquiry.guardian_name else ""

   
    def get_guardian_occupation(self, obj):
        if not obj.enquiry:
            return ""
        latest_followup = obj.enquiry.follow_up_actions.order_by('-followup_date').first()
        if latest_followup and latest_followup.guardian_occupation:
            return latest_followup.guardian_occupation
        return obj.enquiry.occupation or ""
    


class AdmissionCreateSerializer(serializers.ModelSerializer):
    enquiry_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of enquiry IDs to convert to admissions"
    )

    followup_ids = serializers.ListField(     
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
        def get_date_of_birth(self, obj):
            if obj.enquiry and obj.enquiry.date_of_birth:
                return obj.enquiry.date_of_birth.strftime('%d-%m-%Y')
            return None    
   

from django.shortcuts import get_object_or_404

class AdmissionUpdateSerializer(serializers.ModelSerializer):
    enquiry_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    student_name = serializers.CharField()
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    guardian_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    guardian_occupation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone1 = serializers.CharField(max_length=15)
    phone2 = serializers.CharField(max_length=15, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'], required=False)
    educational_qualification = serializers.CharField(max_length=200, required=False)
    university_college = serializers.CharField(max_length=200, required=False, allow_blank=True)
    percentage = serializers.FloatField(required=False, allow_null=True)
    year_of_passing = serializers.IntegerField(required=False, allow_null=True)
    flexible_timings = serializers.CharField(max_length=10, required=False, allow_blank=True)
    class_schedule = serializers.CharField(max_length=100, required=False, allow_blank=True)
   
    
    student_photo = serializers.ImageField(required=False, allow_null=True)
    educational_certificate = serializers.FileField(required=False, allow_null=True)
    aadhaar_copy = serializers.FileField(required=False, allow_null=True)
    
    course_interested = serializers.CharField(max_length=100, write_only=True, required=True, help_text="Accept course ID (number) or course name (string)")
    course_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    admission_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = Admission
        fields = [
            'id', 'enquiry_id', 'student_name', 'date_of_birth', 'guardian_name','guardian_occupation',
            'phone1', 'phone2', 'email', 'address', 'gender',
            'educational_qualification', 'university_college', 'percentage', 'year_of_passing',
            'course_interested','course_fee','student_photo', 'aadhaar_number', 'educational_certificate', 'class_timing', 
            'interested_in_nactet', 'status','flexible_timings','class_timing','nactet_fee','class_schedule','admission_fee','aadhaar_copy'
        ]

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        raw_course = data.pop('course_interested', None)
        if raw_course is None:
            raise serializers.ValidationError({"course_interested": "This field is required."})
        raw_course = str(raw_course).strip()
        if raw_course.isdigit():
            course_id = int(raw_course)
            course_obj = get_object_or_404(course, id=course_id)
        else:
            course_obj = get_object_or_404(course, course_name__iexact=raw_course)
        data['course_interested'] = course_obj
        return data

        

    def get_date_of_birth(self, obj):
        if obj.enquiry and obj.enquiry.date_of_birth:
            return obj.enquiry.date_of_birth.strftime('%d-%m-%Y')
        return None
    
    def update(self, instance, validated_data):
        course_obj = validated_data.pop('course_interested', None)
        
        student_photo = validated_data.pop('student_photo', None)
        educational_certificate = validated_data.pop('educational_certificate', None)
        adhaar_copy = validated_data.pop('aadhaar_copy', None)
    
        
        if student_photo is not None:
            instance.student_photo = student_photo
        if educational_certificate is not None:
            instance.educational_certificate = educational_certificate

        if adhaar_copy is not None:
            instance.aadhaar_copy = adhaar_copy

        enquiry = instance.enquiry
        if enquiry:
            enquiry_fields = [
                'student_name', 'date_of_birth', 'guardian_name',
                'phone1', 'phone2', 'email', 'address', 'gender',
                'educational_qualification', 'university_college', 'percentage',
                'year_of_passing', 
                # 'flexible_timings',
            ]
            for field in enquiry_fields:
                if field in validated_data:
                    setattr(enquiry, field, validated_data.pop(field))
            
            guardian_occupation = validated_data.pop('guardian_occupation', None)
            if guardian_occupation is not None:
                enquiry.occupation = guardian_occupation
                
                followup = FollowUps.objects.filter(enquiry=enquiry).first()
                if followup:
                    followup.guardian_occupation = guardian_occupation
                    followup.save()
                else:
                    FollowUps.objects.create(
                        enquiry=enquiry,
                        enquiry_source=enquiry.heard_from,
                        guardian_occupation=guardian_occupation,
                        status='new'
                    )
                    
            if course_obj:
                enquiry.course_interested = course_obj
            enquiry.save()

        safe_fields = ['class_schedule', 'class_timing', 
                    'interested_in_nactet', 'aadhaar_number', 'status','admission_fee','aadhaar_copy']
        for field in safe_fields:
            if field in validated_data:
                setattr(instance, field, validated_data.pop(field))
                
        if course_obj:
            instance.course = course_obj
            
        instance.nactet_fee = 1000.00 if instance.interested_in_nactet == 'yes' else 0.00
        
        instance.save()
        return instance



    def validate(self, data):
        date_of_birth = data.get('date_of_birth')
        if date_of_birth:
            if date_of_birth > date.today():
                raise serializers.ValidationError({
                    "date_of_birth": "Date of birth cannot be in the future."
                })
            elif date_of_birth.year < 1930:
                raise serializers.ValidationError({
                    "date_of_birth": "Date of birth cannot be before 1930."
                })
        student_name = data.get('student_name', '').strip()
        if len(student_name) < 3 or len(student_name) > 100:
            raise serializers.ValidationError({
                "student_name": "Student name must be between 3 and 100 characters."
            })
        
        guardian_name = data.get('guardian_name', '').strip()
        if guardian_name and (len(guardian_name) < 3 or len(guardian_name) > 100):
            raise serializers.ValidationError({
                "guardian_name": "Guardian name must be between 3 and 100 characters."
            })
        
        contact_number2 = data.get('phone2', '').strip()
        if contact_number2 and len(contact_number2) < 7 or len(contact_number2) > 15:
            raise serializers.ValidationError({
                "phone2": "Contact number 2 must be between 7 and 15 digits."
            })
        email = data.get('email', '').strip()
        if email:
            if len(email) < 5:
                raise serializers.ValidationError({
                    "email": "Email address is too short. Please provide a valid email."
                })
            if len(email) > 100:
                raise serializers.ValidationError({
                    "email": "Email address is too long. Maximum 100 characters allowed."
                })
            if not re.match(r"^[\w\.\+\-']+@[\w\-\.]+\.[a-zA-Z]{2,}$", email):
                raise serializers.ValidationError({
                    "email": "Please enter a valid email address (e.g.) 3l0M5@example.com"
                })

        address = data.get('address', '').strip()
        if address and (len(address) < 5 or len(address) > 300):
            raise serializers.ValidationError({
                "address": "Address must be between 5 and 300 characters."
            })
        qualification = data.get('educational_qualification', '').strip()
        if qualification and (len(qualification) < 3 or len(qualification) > 100):
            raise serializers.ValidationError({
                "educational_qualification": "Educational qualification must be between 3 and 100 characters."
                
            })
        university = data.get('university_college', '').strip()
        if university and (len(university) < 3 or len(university) > 100):
            raise serializers.ValidationError({
                "university_college": "University/College name must be between 3 and 100"
            })
        year_of_passing = data.get('year_of_passing')
        if year_of_passing:
            if year_of_passing < 1930 or year_of_passing > date.today().year:
                raise serializers.ValidationError({
                    "year_of_passing": "Year of passing must be between 1930 and current year."
        
                })
        return data

    def create(self, validated_data):
        course_obj = validated_data.pop('course_interested')
        force_under_review = self.context.get('force_under_review', False) or validated_data.pop('force_under_review', False)
        
        admission_fields = {
            'class_schedule': validated_data.pop('class_schedule', None),
            'class_timing': validated_data.pop('class_timing', None),
            'interested_in_nactet': validated_data.pop('interested_in_nactet', 'no'),
            'status': 'under review' if force_under_review else validated_data.pop('status', 'pending'),
            'aadhaar_number': validated_data.pop('aadhaar_number', None),
            'student_photo': validated_data.pop('student_photo', None),
            'educational_certificate': validated_data.pop('educational_certificate', None),
            'admission_fee': validated_data.pop('admission_fee', None),
            'aadhaar_copy': validated_data.pop('aadhaar_copy', None),
        }
        
        if not validated_data.get('enquiry_id'):
            guardian_occupation = validated_data.pop('guardian_occupation', None)
            
            enquiry_data = {
                'student_name': validated_data.pop('student_name'),
                'date_of_birth': validated_data.pop('date_of_birth', None),
                'guardian_name': validated_data.pop('guardian_name', ''),
                'occupation': guardian_occupation, 
                'phone1': validated_data.pop('phone1'),
                'phone2': validated_data.pop('phone2', ''),
                'email': validated_data.pop('email', ''),
                'address': validated_data.pop('address', ''),
                'gender': validated_data.pop('gender', 'other'),
                'educational_qualification': validated_data.pop('educational_qualification', ''),
                'university_college': validated_data.pop('university_college', ''),
                'percentage': validated_data.pop('percentage', None),
                'year_of_passing': validated_data.pop('year_of_passing', None),
                'flexible_timings': validated_data.pop('flexible_timings', None),
                'course_interested': course_obj,
                


            }
            enquiry_data = {k: v for k, v in enquiry_data.items() if v is not None}
            enquiry = Enquiry.objects.create(**enquiry_data)
            
            if guardian_occupation:
                FollowUps.objects.create(
                    enquiry=enquiry,
                    enquiry_source=enquiry.heard_from,
                    guardian_occupation=guardian_occupation,
                    status='new'
                )
        else:
            enquiry = get_object_or_404(Enquiry, id=validated_data.pop('enquiry_id'))
            guardian_occupation = validated_data.pop('guardian_occupation', None)
            if guardian_occupation is not None:
                enquiry.occupation = guardian_occupation
                enquiry.save()
                
                followup, created = FollowUps.objects.get_or_create(
                    enquiry=enquiry,
                    defaults={
                        'enquiry_source': enquiry.heard_from,
                        'guardian_occupation': guardian_occupation,
                        'status': 'new'
                    }
                )
                if not created:
                    followup.guardian_occupation = guardian_occupation
                    followup.save()
        
      
        admission_data = {k: v for k, v in admission_fields.items() if v is not None}
        admission_data.update({
            'enquiry': enquiry,
            'course': course_obj,
        })
        
        admission = Admission(**admission_data)
        if force_under_review:
            admission.status = 'under review'
            admission.save()
        return admission
    
  





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

 


class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()  
    module_display = serializers.CharField(source='get_module_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'module', 'module_display', 'content', 'created_at', 'is_read']
        read_only_fields = ['created_at', 'is_read', 'module_display']

    def get_created_at(self, obj):
        # Force +5:30 (India Standard Time) – works even if your PC is in UTC
        ist_time = obj.created_at + timedelta(hours=5, minutes=30)
        return ist_time.strftime('%d-%m-%Y %I:%M %p')
    

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['module', 'content']  

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
    rate_change = serializers.CharField()   # ← New
    status = serializers.CharField()



class EnquirySourceStatsSerializer(serializers.Serializer):
    month = serializers.CharField()
    year = serializers.IntegerField()
    sources = serializers.DictField()
    top_source = serializers.CharField()
    top_source_count = serializers.IntegerField()


class PaymentCreateSerializer(serializers.ModelSerializer):
    payment_mode = serializers.ChoiceField(choices=[
        ('cash', 'cash'), ('upi', 'upi'), ('card', 'card'), ('bank transfer', 'bank transfer')
    ])
    transaction_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    receipt_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Payment
        fields = ['payment_mode', 'transaction_id', 'remarks','receipt_type', 'payment_structure']

    def validate(self, data):
        mode = data.get('payment_mode')
        if mode != 'cash' and not data.get('transaction_id'):
            raise serializers.ValidationError({
                "transaction_id": "Transaction ID is required for upi/card/bank transfer."
            })
        return data

    def create(self, validated_data):
        admission = validated_data.pop('admission')
        amount_paid_now = validated_data.pop('amount_paid_now')  # from view

        # Full total: course fee + nactet
        course_fee = admission.course.course_fee or 0
        nactet_fee = 1000 if admission.interested_in_nactet == 'yes' else 0
        total_fee = course_fee + nactet_fee

        return Payment.objects.create(
            admission=admission,
            total_fee_amount=total_fee,
            admission_fee=amount_paid_now,      
            **validated_data
        )
    


class PaidAdmissionListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='enquiry.student_name', read_only=True)
    phone = serializers.CharField(source='enquiry.phone1', read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True, default="Not Assigned")
    admission_fee_paid = serializers.SerializerMethodField()
    

    class Meta:
        model = Admission
        fields = [
            'id',
            'student_code',
            'student_name',
            'phone',
            'course_name',
            'admission_fee',
            'admission_fee_paid',
            'admission_date',

        ]

    def get_admission_fee_paid(self, obj):
        # Returns True if student has paid admission fee (via Payment)
        return Payment.objects.filter(admission=obj).exists()
   

class PaidAdmissionDetailSerializer(serializers.ModelSerializer):
    # Enquiry fields
    student_name = serializers.CharField(source='enquiry.student_name', read_only=True)
    phone = serializers.CharField(source='enquiry.phone1', read_only=True)
    phone2 = serializers.CharField(source='enquiry.phone2', read_only=True)
    email = serializers.CharField(source='enquiry.email', read_only=True, allow_null=True)
    date_of_birth = serializers.DateField(source='enquiry.date_of_birth', read_only=True, format='%d-%m-%Y', allow_null=True)
    gender = serializers.CharField(source='enquiry.gender', read_only=True, allow_null=True)
    guardian_name = serializers.CharField(source='enquiry.guardian_name', read_only=True, allow_null=True)
    guardian_occupation = serializers.SerializerMethodField()
    educational_qualification = serializers.CharField(source='enquiry.educational_qualification', read_only=True)
    address = serializers.CharField(source='enquiry.address', read_only=True, allow_null=True)
    year_of_passing = serializers.IntegerField(source='enquiry.year_of_passing', read_only=True)
    percentage = serializers.FloatField(source='enquiry.percentage', read_only=True)
    university_college = serializers.CharField(source='enquiry.university_college', read_only=True)

    # Course
    course_name = serializers.CharField(source='course.course_name', read_only=True, default="Not Assigned")

    # Payment related
    admission_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount_paid = serializers.SerializerMethodField()
    admission_fee_paid = serializers.SerializerMethodField()  # True/False
    admission_fee_amount_paid = serializers.SerializerMethodField()  # Actual amount paid toward admission fee
    payment_mode = serializers.SerializerMethodField()
    transaction_id = serializers.SerializerMethodField()
    payment_structure = serializers.SerializerMethodField()

    # NACTET
    interested_in_nactet = serializers.CharField(source='get_interested_in_nactet_display', read_only=True)
    nactet_fee = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    # Files with full URLs
    student_photo = serializers.SerializerMethodField()
    aadhaar_copy = serializers.SerializerMethodField()
    educational_certificate = serializers.SerializerMethodField()

    class Meta:
        model = Admission
        fields = [
            'id',  'student_name','student_code', 'admission_date', 'status',
           'phone','phone2', 'email', 'date_of_birth', 'gender','guardian_name','guardian_occupation',
            'educational_qualification', 'address', 'course_name',
            'admission_fee', 'total_amount_paid', 'admission_fee_paid',
            'admission_fee_amount_paid', 'admission_fee_amount_paid',
            'interested_in_nactet', 'nactet_fee',
            'student_photo', 'aadhaar_copy', 'educational_certificate',
            'class_schedule', 'class_timing', 
            'payment_structure',
            'aadhaar_number','payment_mode','year_of_passing','percentage','university_college','transaction_id'
        ]

    def get_guardian_occupation(self, obj):
        if not obj.enquiry:
            return None
        latest_followup = obj.enquiry.follow_up_actions.order_by('-followup_date').first()
        if latest_followup and latest_followup.guardian_occupation:
            return latest_followup.guardian_occupation
        return obj.enquiry.occupation

    def get_student_photo(self, obj):
        if obj.student_photo and hasattr(obj.student_photo, 'url'):
            request = self.context.get('request')
            return request.build_absolute_uri(obj.student_photo.url) if request else obj.student_photo.url
        return None

    def get_aadhaar_copy(self, obj):
        if obj.aadhaar_copy and hasattr(obj.aadhaar_copy, 'url'):
            request = self.context.get('request')
            return request.build_absolute_uri(obj.aadhaar_copy.url) if request else obj.aadhaar_copy.url
        return None

    def get_educational_certificate(self, obj):
        if obj.educational_certificate and hasattr(obj.educational_certificate, 'url'):
            request = self.context.get('request')
            return request.build_absolute_uri(obj.educational_certificate.url) if request else obj.educational_certificate.url
        return None

    def get_total_amount_paid(self, obj):
        """Total paid across all payments for this admission"""
        return Payment.objects.filter(admission=obj).aggregate(
            total=models.Sum('total_fee_amount')
        )['total'] or 0.00

    def get_admission_fee_paid(self, obj):
        """Returns True if any payment exists (simple boolean)"""
        return Payment.objects.filter(admission=obj).exists()

    def get_admission_fee_amount_paid(self, obj):
        """Actual sum of admission_fee field from Payment model (if you're storing it per payment)"""
        return Payment.objects.filter(admission=obj).aggregate(
            total=models.Sum('admission_fee')
        )['total'] or 0.00
    
    def get_payment_mode(self, obj):
        latest_payment = Payment.objects.filter(admission=obj).order_by('-payment_date').first()
        if latest_payment:
            return latest_payment.payment_mode
        return None
    
    def get_transaction_id(self, obj):
        latest_payment = Payment.objects.filter(admission=obj).order_by('-payment_date').first()
        if latest_payment:
            return latest_payment.transaction_id
        return None
    def get_payment_structure(self, obj):
        latest_payment = Payment.objects.filter(admission=obj).order_by('-payment_date').first()
        if latest_payment:
            return latest_payment.get_payment_structure_display()
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Only include nactet_fee if interested_in_nactet == 'yes'
        if data['interested_in_nactet'].lower() != 'yes':
            data.pop('nactet_fee', None)
        
        return data 


from django.core.exceptions import ValidationError
from django.db import transaction

class PaidAdmissionUpdateSerializer(serializers.ModelSerializer):
    # Enquiry fields (writable)
    student_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.CharField(                     # ← Changed to CharField
        required=False, allow_blank=True, allow_null=True,
        help_text="Format: dd-mm-yyyy (e.g. 15-08-1998)"
    )
    guardian_name = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    phone1 = serializers.CharField(max_length=15)
    phone2 = serializers.CharField(max_length=15, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    gender = serializers.ChoiceField(choices=Enquiry.GENDER_CHOICES, required=False, allow_null=True)
    educational_qualification = serializers.CharField(max_length=200)
    university_college = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    percentage = serializers.FloatField(required=False, allow_null=True)
    year_of_passing = serializers.IntegerField(required=False, allow_null=True)

    # Course by name instead of ID
    course = serializers.CharField(required=False, allow_blank=True)   # ← Now accepts name!

    class_schedule = serializers.ChoiceField(choices=Admission.SCHEDULE_CHOICES, required=False, allow_null=True)
    class_timing = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    payment_structure = serializers.ChoiceField(choices=Payment.PAYMENT_STRUCTURE_CHOICES, required=False, allow_null=True)
    interested_in_nactet = serializers.ChoiceField(choices=Admission.NACTIT_CHOICES, required=False)

    # File fields
    student_photo = serializers.ImageField(required=False, allow_empty_file=True)
    aadhaar_copy = serializers.FileField(required=False, allow_empty_file=True)
    educational_certificate = serializers.FileField(required=False, allow_empty_file=True)
    aadhaar_number = serializers.CharField(
        max_length=12, required=False, allow_blank=True,
        validators=[RegexValidator(r'^\d{12}$', 'Aadhaar must be exactly 12 digits')]
    )

    class Meta:
        model = Admission
        fields = [
            'student_name', 'date_of_birth', 'guardian_name', 'phone1', 'phone2',
            'email', 'address', 'gender', 'educational_qualification',
            'university_college', 'percentage', 'year_of_passing',
            'course', 'class_schedule', 'class_timing',
              'payment_structure',
            'interested_in_nactet', 'aadhaar_number',
            'student_photo', 'aadhaar_copy', 'educational_certificate',
        ]

    
    def validate_date_of_birth(self, value):
        if not value:
            return None
        try:
            return dt_module.datetime.strptime(value, "%d-%m-%Y").date()
        except ValueError:
            raise serializers.ValidationError("Date must be in dd-mm-yyyy format (e.g. 25-12-1999)")
    def validate_course(self, value):
        if not value:
            return None
        try:
            return course.objects.get(course_name__iexact=value.strip())
        except course.DoesNotExist:
            raise serializers.ValidationError(f"Course '{value}' not found.")

    @transaction.atomic
    def update(self, instance, validated_data):
        # Handle date_of_birth (converted in validate_date_of_birth)
        if 'date_of_birth' in validated_data:
            instance.enquiry.date_of_birth = validated_data.pop('date_of_birth')

        # Handle course (converted in validate_course)
        if 'course' in validated_data:
            instance.course = validated_data.pop('course')

        # Extract enquiry data safely
        enquiry_data = {
            'student_name': validated_data.pop('student_name', instance.enquiry.student_name),
            'phone1': validated_data.pop('phone1', instance.enquiry.phone1),
            'date_of_birth': instance.enquiry.date_of_birth,  # already handled above
            'guardian_name': validated_data.pop('guardian_name', instance.enquiry.guardian_name),
            'phone2': validated_data.pop('phone2', instance.enquiry.phone2),
            'email': validated_data.pop('email', instance.enquiry.email),
            'address': validated_data.pop('address', instance.enquiry.address),
            'gender': validated_data.pop('gender', instance.enquiry.gender),
            'educational_qualification': validated_data.pop('educational_qualification', instance.enquiry.educational_qualification),
            'university_college': validated_data.pop('university_college', instance.enquiry.university_college),
            'percentage': validated_data.pop('percentage', instance.enquiry.percentage),
            'year_of_passing': validated_data.pop('year_of_passing', instance.enquiry.year_of_passing),
        }

        # Update Enquiry
        enquiry = instance.enquiry
        for attr, value in enquiry_data.items():
            if value is not None:  # Only update if value was provided or defaulted
                setattr(enquiry, attr, value)
        enquiry.save()

        # Handle NACTET
        if 'interested_in_nactet' in validated_data:
            instance.interested_in_nactet = validated_data.pop('interested_in_nactet')
            instance.nactet_fee = 1000.00 if instance.interested_in_nactet == 'yes' else 0.00

        # Update remaining fields (files, aadhaar_number, class_schedule, etc.)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class AdmisionNotificationSerializer(serializers.ModelSerializer):
    class meta:
        models = Notification
        fields = ['id','module','content','created_at','is_read']






        











