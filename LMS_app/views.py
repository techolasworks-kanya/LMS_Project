import decimal
from django.shortcuts import render
from rest_framework import generics
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login
from rest_framework.permissions import AllowAny
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView  
from rest_framework.pagination import PageNumberPagination

def create_notification(module, content, admission=None):
    """Create notification with auto-expiry and smart deduplication"""
    # Avoid duplicates for same admission + similar message
    if admission:
        existing = Notification.objects.filter(
            admission=admission,
            module=module,
            content__icontains=content.split("Missing:")[0] if "Missing" in content else content[:50],
            created_at__gte=timezone.now() - timedelta(hours=2)  # Avoid spam in 2 hours
        ).first()

        if existing:
            # Refresh expiry
            existing.auto_expire_at = timezone.now() + timedelta(days=30)
            existing.is_read = False
            existing.save()
            return existing

    return Notification.objects.create(
        module=module,
        content=content,
        admission=admission,
        auto_expire_at=timezone.now() + timedelta(days=30)
    )

def create_document_pending_notification(admission):
    missing = []
    # if not admission.student_photo:
    #     missing.append("Passport Size Photo")
    # if not admission.aadhaar_copy:
    #     missing.append("Aadhaar Card Copy")
    if not admission.educational_certificate:
        missing.append("Educational Certificate")

    if missing:
        student_name = admission.enquiry.student_name if admission.enquiry else "Unknown"
        course_name = admission.course.course_name if admission.course else "Unknown Course"

        content = f"Documents pending for {student_name} ({course_name}) — Missing: {', '.join(missing)}"

        create_notification(module='admission', content=content, admission=admission)


def trigger_fee_pending_notification(admission):
    if admission.admission_fee > 0 and admission.fee_paid < admission.admission_fee:
        content = f"Admission fee pending: {admission.enquiry.student_name} owes ₹{admission.admission_fee - admission.fee_paid}"
        create_notification('admission', content, admission)

def trigger_non_confirmed_notifications():
    pending = Admission.objects.filter(
        is_deleted=False,
        status__in=['pending', 'under review'],
        admission_date__lte=timezone.now().date() - timedelta(days=3)  # 3+ days old
    )
    for adm in pending:
        content = f"Admission pending confirmation: {adm.enquiry.student_name} ({adm.course.course_name})"
        create_notification('admission', content, adm)



@api_view(['GET'])
def server_running(request):
    return Response({"message": "Server running"})



class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        # ----- 1. Detect first login via temp_password attribute -----
        is_first_login = hasattr(user, 'temp_password') and user.temp_password is not None

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Build response
        role = 'Superadmin' if user.is_superuser else (user.job_title or 'User')
        response_data = {
            "message": f"{role} logged in successfully",
            "email": user.email,
            "job_title": user.job_title,
            "reset_password_required":True if is_first_login else False,
            # "is_superuser": user.is_superuser,
        }

        # Add reset-password flag only on first login
        if is_first_login:
            response_data["reset_password_required"] = True
            response_data["message"] = "Login successful. Please reset your password."

        response = Response(response_data, status=200)

        # Set HttpOnly cookies
        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax', max_age=86400)
        response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax', max_age=604800)

        return response
    

class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Verify old password
        if not request.user.check_password(old_password):
            return Response({"error": "Current password is incorrect"}, status=400)

        # Set new password
        request.user.set_password(new_password)
        request.user.temp_password = None   # <-- clear flag
        request.user.save()

        # Issue fresh tokens
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({"message": "Password changed successfully"}, status=200)
        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax', max_age=86400)
        response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax', max_age=604800)

        return response

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"error": "No refresh token"}, status=401)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            response = Response({"message": "Token refreshed"})
            response.set_cookie('access_token', access_token, httponly=True, samesite='Lax', max_age=86400)
            return response
        except:
            return Response({"error": "Invalid refresh token"}, status=401)


class UserLogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
class CreateUserAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superadmin can create users or admins."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": f"{user.job_title} created successfully",
                "user": {
                    "name": user.name,
                    "email": user.email,
                    "job_title": user.job_title,
                    "password": getattr(user, 'temp_password', None)
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#certfication
class CertficationListCreateView(generics.ListCreateAPIView):
    queryset = certfication.objects.all()
    serializer_class = EnquiryCreateSerializer
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CertficationSerializer
        return 

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            "status": "Course created successfully.",
            "data": response.data
        }
        return response


# Course
class CourseListCreateView(generics.ListCreateAPIView):
    queryset = course.objects.all()
    

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CourseCreateSerializer
        return CourseListSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            "status": "Course created successfully.",
            "data": response.data
        }
        return response

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = course.objects.all()
    serializer_class = CourseCreateSerializer
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            "status": "Course updated successfully.",
            "data": response.data
        }
        return response

from django.db.models import Exists, OuterRef


class EnquiryListCreateView(generics.ListCreateAPIView):
    queryset = Enquiry.objects.all()
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        return EnquiryCreateSerializer if self.request.method == 'POST' else EnquiryListSerializer

    def get_queryset(self):
        if self.request.method == 'GET':
            has_followup = Exists(
                FollowUps.objects.filter(enquiry_id=OuterRef('pk'))
            )
            return Enquiry.objects.exclude(
                admissions__isnull=False
            
            ).exclude(
                is_archived=True                     
            ).exclude(
                has_followup             
            ).select_related('course_interested').order_by('-id')
        
        return super().get_queryset()


    def perform_create(self, serializer):
        enquiry = serializer.save()  
        course_name = (
            enquiry.course_interested.course_name 
            if enquiry.course_interested else "Unknown Course"
        )
        notification_content = f"New enquiry received for {course_name} from {enquiry.student_name}"

        Notification.objects.create(
            module='enquiry',
            content=notification_content,
            is_read=False
        )
        return enquiry
    

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enquiry = self.perform_create(serializer)

        response_data = {
            "student_name": enquiry.student_name,
            "heard_from": enquiry.heard_from,
            "date_of_birth": enquiry.date_of_birth,
            "course_interested": (
                enquiry.course_interested.course_name
                if enquiry.course_interested else None
            ),
        }

        if not serializer.is_valid():
            return Response({
                "status": "Enquiry creation failed",
                "message": "Please correct the errors below",
                "errors": serializer.errors 
            }, status=status.HTTP_400_BAD_REQUEST)


        return Response({
            "status": "Enquiry created successfully",
            "data": response_data
        }, status=status.HTTP_201_CREATED)
    

#todays enquirires and count  - if zero enqur
class TodayEnquiryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = EnquiryListSerializer

    def get_queryset(self):
        today = timezone.now().date()
        today_count  = Enquiry.objects.filter(enquiry_date=today).count()
        return Enquiry.objects.filter(
            enquiry_date=today
        ).select_related('course_interested').order_by('-id')
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        today_count  = Enquiry.objects.filter(enquiry_date=timezone.now().date()).count()
        return Response({
            "today_enquiries_count": today_count,
            "data": serializer.data
        })



    # def get_queryset(self):
    #     today = timezone.now().date()
    #     return Enquiry.objects.filter(
    #         enquiry_date=today
    #     ).select_related('course_interested').order_by('-id')


from django.db.models import OuterRef, Exists, Subquery



class EnquiryStatusListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        latest_admission = Admission.objects.filter(
            enquiry=OuterRef('pk'),
            is_deleted=False
        ).order_by('-admission_date')

        latest_followup = FollowUps.objects.filter(
            enquiry=OuterRef('pk')
        ).order_by('-followup_date')

        from django.db.models import Q
        
        enquiries = Enquiry.objects.filter(is_archived=False).annotate(
            has_admission=Exists(Admission.objects.filter(enquiry=OuterRef('pk'), is_deleted=False)),
            admission_date=Subquery(latest_admission.values('admission_date')[:1]),

            has_followup=Exists(FollowUps.objects.filter(enquiry=OuterRef('pk'))),
            latest_followup_date=Subquery(latest_followup.values('followup_date')[:1]),
        ).filter(
            Q(has_followup=True) | Q(has_admission=True)
        ).select_related('course_interested').order_by('-enquiry_date')

        results = []
        for enquiry in enquiries:
            if enquiry.has_admission:
                status_label = "admission"
                conversion_date = enquiry.admission_date.strftime("%d-%m-%Y") if enquiry.admission_date else None
            else:
                status_label = "followup"
                conversion_date = None  # HIDE date for follow-up only

            results.append({
                "id": enquiry.id,
                "student_name": enquiry.student_name or "No Name",
                "enquiry_date": enquiry.enquiry_date.strftime("%d-%m-%Y"),
                "course_name": enquiry.course_interested.course_name if enquiry.course_interested else "Not Selected",
                "heard_from": enquiry.get_heard_from_display() if enquiry.heard_from else "Not Specified",
                "status": status_label,
                "conversion_date": conversion_date,  # Only shown when status = admission
            })

        return Response(results)



class EnquiryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquiryCreateSerializer
    permission_classes = [AllowAny]

   
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            "status": "Enquiry updated successfully.",
            "data": response.data
        }
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"status": "Enquiry deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )





# Follow-up List and Create
class FollowUpListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        if self.request.method == 'GET':
            return FollowUps.objects.select_related(
                'enquiry', 'enquiry__course_interested'
            ).prefetch_related('remarks').exclude(
            enquiry__admissions__status='confirmed'
        ).order_by('-id')
        return super().get_queryset()

    
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        return FollowUpListSerializer if self.request.method == 'GET' else FollowUpDetailSerializer

    def perform_create(self, serializer):
        enquiry_ids = serializer.validated_data.pop('enquiry_ids')
        remarks = serializer.validated_data.pop('remarks', [])

        enquiries = Enquiry.objects.filter(id__in=enquiry_ids,follow_up_actions__isnull=True)
        found_ids = enquiries.values_list('id', flat=True)
        missing = set(enquiry_ids) - set(found_ids)
        if missing:
            raise serializers.ValidationError({
                "enquiry_ids": f"Enquiries with IDs {list(missing)} not found or already converted."
            })

        created_followups = []
        for enquiry in enquiries:
            followup = FollowUps.objects.create(
                enquiry=enquiry,
                enquiry_source=enquiry.heard_from,
                status=serializer.validated_data.get('status', 'new'),
                next_followup_date=serializer.validated_data.get('next_followup_date')
            )

            # Add remarks
            for content in remarks:
                if content.strip():
                    FollowUpRemark.objects.create(followup=followup, content=content.strip())

            created_followups.append(followup)

     

        self.created_followups = created_followups

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_data = FollowUpListSerializer(
            self.created_followups, many=True, context={'request': request}
        ).data

        return Response({
            "status": f"{len(self.created_followups)} follow-up(s) created successfully",
            "data": response_data
        }, status=status.HTTP_201_CREATED)
    

class FollowUpDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FollowUps.objects.select_related(
        'enquiry', 'enquiry__course_interested'
    ).prefetch_related('remarks')
    serializer_class = FollowUpDetailSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        # Validate and update followup fields
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        followup = serializer.save()

        validated_data = serializer.validated_data

        # --- UPDATE ENQUIRY NESTED FIELDS ---
        enquiry_data = validated_data.pop('enquiry', None)
        if enquiry_data:
            enquiry_serializer = EnquiryNestedUpdateSerializer(
                instance.enquiry, data=enquiry_data, partial=True
            )
            enquiry_serializer.is_valid(raise_exception=True)
            enquiry_serializer.save()

        

        # --- RELOAD UPDATED FOLLOW-UP WITH REMARKS & ENQUIRY ---
        followup = FollowUps.objects.prefetch_related('remarks').get(pk=instance.pk)
        followup.enquiry = Enquiry.objects.select_related('course_interested').get(pk=followup.enquiry.pk)

        # --- RETURN SUCCESS RESPONSE ---
        output = FollowUpListSerializer(followup, context=self.get_serializer_context()).data

        return Response({
            "status": "Follow-up updated successfully",
            "data": output
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        followup = self.get_object()          # the FollowUp
        enquiry = followup.enquiry 
        enquiry.delete()


      
        return Response(
            {"status": "Follow-up and enquiry deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        ) 



# Admission
class AdmissionListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        queryset = Admission.objects.select_related(
            'enquiry', 'enquiry__course_interested'
        ).filter(is_deleted=False)
        queryset = queryset.exclude(payments__isnull=False)

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        if month and year:
            queryset = queryset.filter(
                admission_date__month=month,
                admission_date__year=year
            )

        return queryset.order_by('-id')
    
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        return AdmissionListSerializer if self.request.method == 'GET' else AdmissionCreateSerializer

    def perform_create(self, serializer):
        followup_ids = serializer.validated_data.pop('followup_ids', None)
        enquiry_ids = serializer.validated_data.pop('enquiry_ids', None)

        # ---------------------------------------------------
        # 1) FOLLOWUPS → ADMISSIONS
        # ---------------------------------------------------
        if followup_ids:
            followups = FollowUps.objects.filter(id__in=followup_ids)

            if followups.count() != len(followup_ids):
                raise serializers.ValidationError(
                    {"followup_ids": "One or more followups do not exist."}
                )

            created_admissions = []

            for followup in followups:
                if followup.status != "interested":
                    raise serializers.ValidationError(
                        {"followup_ids": f"Follow-up {followup.id} is not 'interested'."}
                    )

                enquiry = followup.enquiry

                admission = Admission.objects.create(
                    enquiry=enquiry,
                    course=enquiry.course_interested,
                    fee_paid=0,
                    status="pending"
                )

                created_admissions.append(admission)

                followup.delete()

            self.created_admissions = created_admissions
            return

    # 2) OLD LOGIC: ENQUIRIES → ADMISSIONS
        if enquiry_ids:
            enquiries = Enquiry.objects.filter(
                id__in=enquiry_ids,
                follow_up_actions__isnull=True,
                admissions__isnull=True
            )

            found_ids = enquiries.values_list('id', flat=True)
            missing = set(enquiry_ids) - set(found_ids)
            if missing:
                raise serializers.ValidationError({
                    "enquiry_ids": f"Enquiries {list(missing)} not found or already converted."
                })

            created_admissions = []

            for enquiry in enquiries:
                admission = Admission.objects.create(
                    enquiry=enquiry,
                    course=enquiry.course_interested,
                    fee_paid=0,
                    status="pending"
                )
                created_admissions.append(admission)


                create_notification(
                    module='admission',
                    content=f"New admission created: {admission.enquiry.student_name} - {admission.course.course_name}",
                    admission=admission
                )

            self.created_admissions = created_admissions
            return

       
        raise serializers.ValidationError(
            "Either 'followup_ids' or 'enquiry_ids' is required."
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_data = AdmissionListSerializer(
            self.created_admissions, many=True
        ).data

        return Response({
            "status": f"{len(self.created_admissions)} admission(s) created successfully",
            "data": response_data
        }, status=status.HTTP_201_CREATED)

class AdmissionDetailView(generics.RetrieveAPIView):
    queryset = Admission.objects.select_related('enquiry', 'enquiry__course_interested')
    serializer_class = AdmissionListSerializer
    permission_classes = [AllowAny]

class AdmissionUpdateView(generics.UpdateAPIView):
    queryset = Admission.objects.select_related('enquiry', 'enquiry__course_interested','course').prefetch_related('enquiry__follow_up_actions')
    serializer_class = AdmissionUpdateSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'


   
    def post(self, request, *args, **kwargs):
        if not kwargs.get('id'):
            # Combine data and files
            data = request.data.copy()
            data.update(request.FILES)
            
            serializer = self.get_serializer(data=data, context={'force_under_review': True})
            serializer.is_valid(raise_exception=True)
            
            admission = serializer.save(force_under_review=True)
            full_data = AdmissionListSerializer(admission, context={'request': request}).data

            create_notification(
                module='admission',
                content=f"New admission created: {admission.enquiry.student_name} - {admission.course.course_name}",
                admission=admission
            )

            return Response({
                "status": "Manual admission created successfully!",
                "data": full_data
            }, status=201)

        return self.patch(request, *args, **kwargs)

   
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_deleted:
            return Response({"error": "Cancelled admission cannot be updated"}, status=400)

        data = request.data.copy()
        data.update(request.FILES)

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_admission = serializer.save()
        
        if updated_admission.status not in ['confirmed', 'cancelled']:
            updated_admission.status = 'under review'
            updated_admission.save(update_fields=['status'])
            updated_admission.refresh_from_db()

        full_data = AdmissionListSerializer(updated_admission, context={'request': request}).data   
        # TRIGGER NOTIFICATION IF STILL MISSING DOCS
        create_document_pending_notification(updated_admission)
        return Response({
            "status": "Admission updated successfully",
            "data": full_data
        }, status=200)


class AdmissionDeleteView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "IDs required"}, status=400)

        # SOFT DELETE — never hard delete
        updated = Admission.objects.filter(id__in=ids).update(is_deleted=True, status='cancelled')
        
        return Response({
            "message": f"{updated} admission(s) cancelled successfully"
        }, status=200)


class AdmissionPaymentInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, admission_id=None):
        admission = get_object_or_404(Admission, id=admission_id, is_deleted=False)

        # Get course name
        if admission.course:
            course_name = admission.course.course_name
            course_fee = admission.course.course_fee or Decimal('0.00')
        elif admission.enquiry and admission.enquiry.course_interested:
            course_name = admission.enquiry.course_interested.course_name
            course_fee = admission.enquiry.course_interested.course_fee or Decimal('0.00')
        else:
            course_name = "Not Selected"
            course_fee = Decimal('0.00')

        # NACTET fee
        nactet_fee = Decimal('1000.00') if admission.interested_in_nactet == 'yes' else Decimal('0.00')

        # Total amount = course + nactet
        total_amount = course_fee + nactet_fee

        # Admission fee (registration fee)
        admission_fee = admission.admission_fee or Decimal('0.00')

        return Response({
            "course_name": course_name,
            "total_amount": f"{total_amount:.2f}",
            "admission_fee": f"{admission_fee:.2f}"
        })

#enquiry to followup , enquiry to admision converted count for each month show all monts count 
class MonthlyEnquiryToAdmissionConversionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.now()
        current_year = today.year
        current_month = today.month

        results = []

        for i in range(12):
            # Calculate target month and year by going backwards
            target_month = current_month - i
            target_year = current_year

            # Adjust year if month goes below 1
            if target_month <= 0:
                target_month += 12
                target_year -= 1

            # Count admissions from enquiries in that month/year
            conversion_count = Admission.objects.filter(
                enquiry__enquiry_date__year=target_year,
                enquiry__enquiry_date__month=target_month
            ).count()

            #conversion rate also needed
            total_enquiries = Enquiry.objects.filter(enquiry_date__year=target_year, enquiry_date__month=target_month).count()
            if total_enquiries > 0:
                conversion_rate = round((conversion_count / total_enquiries) * 100)
            else:
                conversion_rate = 0

            results.append({
                "month": calendar.month_name[target_month],
                "short_month": calendar.month_abbr[target_month],
                "year": target_year,
                "month_year": f"{calendar.month_abbr[target_month]} {target_year}",
                "conversion_count": conversion_count,
                "conversion_rate": f"{conversion_rate}%"

            })

        results.reverse()  #

        return Response({
            "monthly_conversions": results
        })
    

# NOT INTERESTED LEAD
class NotInterestedLeadCreateView(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        followup_ids = request.data.get('followup_ids', None)

        if not followup_ids:
            return Response({"error": "'followup_ids' is required"}, status=400)

        if not isinstance(followup_ids, list):
            return Response({"error": "'followup_ids' must be a list of integers"}, status=400)

        followups = FollowUps.objects.select_related('enquiry').filter(id__in=followup_ids)

        # validate all followups exist
        if followups.count() != len(followup_ids):
            return Response({"error": "One or more followups not found"}, status=404)

        created_records = []

        for followup in followups:

            # Follow-up must already be saved with "not_interested"
            if followup.status != "not_interested":
                return Response(
                    {"error": f"Follow-up {followup.id} is not marked as 'not_interested'"},
                    status=400
                )

            # Prevent duplicates
            if NotInterestedLead.objects.filter(followup=followup).exists():
                return Response({"error": f"Follow-up {followup.id} already archived"}, status=400)

            # SAVE DATA INTO NOT INTERESTED TABLE
            record = NotInterestedLead.objects.create(
                followup=followup,
                enquiry=followup.enquiry,
                last_followup_date=followup.followup_date,
                status="not_interested"
            )
            followup.enquiry.is_archived = True
            followup.enquiry.save(update_fields=['is_archived'])        

            followup.delete()
            created_records.append(record)

             # 1️⃣ UPDATE ENQUIRY STATUS
            # followup.enquiry.status = "not_interested"
            # followup.enquiry.save()

            # NOW delete only followup (NOT enquiry)
            
            

        return Response({
            "status": "Success",
            "message": f"{len(created_records)} followup(s) moved to Not Interested",
            "data": [r.id for r in created_records]
        }, status=201)

# LIST with SEARCH
class NotInterestedLeadListView(generics.ListAPIView):
    serializer_class = NotInterestedLeadListSerializer
    permission_classes = [AllowAny]
    # pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = NotInterestedLead.objects.select_related(
            'followup', 'enquiry', 'enquiry__course_interested'
        )
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                enquiry__student_name__icontains=search
            )
        return queryset.order_by('-id')
    
    

# NOTIFICATIONS
class NotificationCreateView(generics.CreateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save(
            
            object_id=None,
            content_type=None
        )
        return Response({
            "status": "Notification created",
            "data": NotificationSerializer(notification).data
        }, status=status.HTTP_201_CREATED)


class NotificationAllListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # ONLY ENQUIRY MODULE — Admission notifications are hidden here
        return Notification.objects.filter(
            module='enquiry'
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        unread_count = queryset.filter(is_read=False).count()

        return Response({
            "unread_count": unread_count,
            "notifications": serializer.data
        })



# OPEN → AUTO MARK READ
class NotificationDetailView(generics.RetrieveAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=['is_read'])
        return Response(NotificationSerializer(instance).data)
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=['is_read'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NotificationUpdateView(generics.UpdateAPIView):
        
    queryset = Notification.objects.all()
    serializer_class = NotificationUpdateSerializer
    permission_classes = [AllowAny]

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)



# This shows ONLY ADMISSION notifications (separate section/tab)
class AdmissionNotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Notification.objects.filter(
            module='admission'
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        unread_count = queryset.filter(is_read=False).count()

        return Response({
            "unread_count": unread_count,
            "notifications": serializer.data
        })


import calendar
from datetime import timedelta, date



class ConversionStatsView(APIView):
    def get(self, request):
        today = date.today()
        current_month = today.month
        current_year = today.year

       
        prev_date = (today.replace(day=1) - timedelta(days=1))
        prev_month = prev_date.month
        prev_year = prev_date.year

        # === CURRENT MONTH ===
        current_enquiries = Enquiry.objects.filter(
            enquiry_date__month=current_month,
            enquiry_date__year=current_year
        ).count()

        current_admissions = Admission.objects.filter(
            enquiry__enquiry_date__month=current_month,
            enquiry__enquiry_date__year=current_year
        ).count()

        current_rate = round((current_admissions / current_enquiries) * 100) if current_enquiries > 0 else 0

        # === PREVIOUS MONTH ===
        prev_enquiries = Enquiry.objects.filter(
            enquiry_date__month=prev_month,
            enquiry_date__year=prev_year
        ).count()

        prev_admissions = Admission.objects.filter(
            enquiry__enquiry_date__month=prev_month,
            enquiry__enquiry_date__year=prev_year
        ).count()

        prev_rate = round((prev_admissions / prev_enquiries) * 100) if prev_enquiries > 0 else 0

        change = current_rate - prev_rate

        if change > 0:
            rate_change = f"{change}%"
            status = "increased"
        elif change < 0:
            rate_change = f"{change}%"
            status = "decreased"
        else:
            rate_change = "0%"
            status = "no change"

        data = {
            "month": calendar.month_name[current_month],
            "year": current_year,
            "total_enquiry": current_enquiries,
            "total_admission": current_admissions,
            "admission_rate": f"{current_rate}%",
            "rate_change": rate_change,      
            "status": status
        }

        serializer = ConversionStatsSerializer(data)
        return Response(serializer.data)



from collections import Counter
class EnquirySourceStatsView(APIView):
    def get(self, request):

        today = date.today()
        month = today.month
        year = today.year

        enquiries = Enquiry.objects.filter(
            enquiry_date__month=month,
            enquiry_date__year=year
        )

        source_counts = Counter(enq.heard_from for enq in enquiries)

        # Total enquiries of the month
        total = sum(source_counts.values())

        # Compute percentage + count
        source_stats = {}
        for source, count in source_counts.items():
            percentage = round((count / total) * 100) if total > 0 else 0
            source_stats[source] = {
                "count": count,
                "percentage": percentage
            }

        # Find top source platform
        if total > 0:
            top_source = max(source_counts, key=source_counts.get)
            top_count = source_counts[top_source]
        else:
            top_source = None
            top_count = 0

        data = {
            "month": calendar.month_name[month],
            "year": year,
            "sources": source_stats,
            "top_source": top_source,
            "top_source_count": top_count
        }

        serializer = EnquirySourceStatsSerializer(data)
        return Response(serializer.data)

from  io import BytesIO
import datetime   
from django.db.models import Q  
class ExportEnquiryExcel(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        header_image = request.FILES.get("header_image")  

        latest_admission = Admission.objects.filter(
            enquiry=OuterRef('pk'),
            is_deleted=False
        ).order_by('-admission_date')

        latest_followup = FollowUps.objects.filter(
            enquiry=OuterRef('pk')
        ).order_by('-followup_date')

        enquiries = Enquiry.objects.filter(is_archived=False).annotate(
            has_admission=Exists(Admission.objects.filter(enquiry=OuterRef('pk'), is_deleted=False)),
            admission_date=Subquery(latest_admission.values('admission_date')[:1]),
            has_followup=Exists(FollowUps.objects.filter(enquiry=OuterRef('pk'))),
            latest_followup_date=Subquery(latest_followup.values('followup_date')[:1]),
        ).filter(
            Q(has_followup=True) | Q(has_admission=True)
        ).select_related('course_interested').order_by('-enquiry_date')

        # === Create Excel Workbook ===
        wb = Workbook()
        ws = wb.active
        ws.title = "Enquiry Status Report"

        # Column settings
        columns = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for col in columns:
            ws.column_dimensions[col].width = 22

        table_start_row = 5

        # Optional Header Image
        if header_image:
            try:
                img = XLImage(header_image)
                img.width = 720  
                img.height = 170
                ws.row_dimensions[1].height = 60
                ws.row_dimensions[2].height = 60
                ws.row_dimensions[3].height = 60
                ws.add_image(img, "A1")
                table_start_row = 5
            except Exception as e:
                return Response(
                    {"error": f"Invalid image file: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Title
        ws.cell(row=table_start_row - 1, column=1).value = "Enquiry Status Report (Follow-ups & Admissions)"
        ws.cell(row=table_start_row - 1, column=1).font = ws.cell(row=table_start_row - 1, column=1).font.copy(
            bold=True, size=14
        )
        ws.merge_cells(start_row=table_start_row - 1, start_column=1, end_row=table_start_row - 1, end_column=7)

        # Header Row
        headers = [
            "Student Name",
            "Enquiry Date",
            "Course Interested",
            "Heard From",
            "Current Status",
            "Conversion Date",  
            "Phone"
        ]
        header_row = table_start_row
        for idx, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=idx, value=header)
            cell.font = cell.font.copy(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

        # Data Rows
        data_row = header_row + 1
        for enquiry in enquiries:
            if enquiry.has_admission:
                status = "Admission"
                conversion_date = enquiry.admission_date.strftime("%d-%m-%Y") if enquiry.admission_date else "-"
            else:
                status = "Follow-up"
                conversion_date = "-"  

            ws.append([
                enquiry.student_name or "No Name",
                enquiry.enquiry_date.strftime("%d-%m-%Y"),
                enquiry.course_interested.course_name if enquiry.course_interested else "Not Selected",
                enquiry.get_heard_from_display() if hasattr(enquiry, 'get_heard_from_display') else enquiry.heard_from,
                status,
                conversion_date,
                enquiry.phone1,
            ])

        # Footer: Total count
        total = enquiries.count()
        ws.append([])
        ws.append([f"Total Records: {total}", "", "", "", "", "", "Generated on: " + datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p")])

        # === Save to memory and return file ===
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            content=output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"enquiry_status_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


import openpyxl
from openpyxl.drawing.image import Image as XLImage
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import date
import calendar
class ExportAdmissionExcel(APIView):
    def post(self, request, *args, **kwargs):

        header_image = request.FILES.get("header_image")

        wb = Workbook()
        ws = wb.active
        ws.title = "Admissions"

       
        total_columns = 6
        column_width = 35

        for col in range(1, total_columns + 1):
            ws.column_dimensions[get_column_letter(col)].width = column_width

        if header_image:
            try:
                img = XLImage(header_image)

                total_excel_pixels = column_width * total_columns * 6
                img.width = total_excel_pixels

                ws.row_dimensions[1].height = 55
                ws.row_dimensions[2].height = 55
                ws.row_dimensions[3].height = 55

                img.height = 170

                ws.add_image(img, "A1")

            except Exception as e:
                return Response(
                    {"error": f"Invalid image file: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            table_start_row = 5
        else:
            table_start_row = 1

        # ---------------------------
        # Table Header Styling
        # ---------------------------
        headers = ["Student Name", "Course", "Phone", "Email", "Date"]

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="4F81BD")  # Blue header
        header_align = Alignment(horizontal="center", vertical="center")

        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        # Write header row
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=table_start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border

        
        # Add Admission Data
        # ---------------------------
        admissions = Admission.objects.select_related("enquiry")

        row = table_start_row + 1

        for adm in admissions:
            values = [
                adm.enquiry.student_name,
                adm.enquiry.course_interested.course_name if adm.enquiry.course_interested else "",
                adm.enquiry.phone1,
                adm.enquiry.email,
                adm.admission_date.strftime("%d-%m-%Y"),
            ]

            for col, val in enumerate(values, start=1):
                cell = ws.cell(row=row, column=col, value=val)
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")

            row += 1

        # Return Excel Download
        
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="admissions.xlsx"'

        wb.save(response)
        return response

    def post(self, request, *args, **kwargs):
        header_image = request.FILES.get("header_image")

        # Current month & year
        today = date.today()
        month_name = calendar.month_name[today.month]
        year = today.year

        # Fetch enquiries for current month
        enquiries = Enquiry.objects.filter(
            enquiry_date__year=year,
            enquiry_date__month=today.month
        ).select_related('course_interested').order_by('enquiry_date')

        wb = Workbook()
        ws = wb.active
        ws.title = "Enquiry Source Tracking"

        start_row = 1

        # === 1. Add Header Image (Full Width) ===
        if header_image:
            try:
                img = XLImage(header_image)
                img.width = 920   # Perfect fit for A to H columns
                img.height = 150
                ws.row_dimensions[1].height = 112
                ws.add_image(img, "A1")
                start_row = 6  # Leave space below image
            except Exception as e:
                return HttpResponse(f"Invalid image: {e}", status=400)

        # === 2. Title on the Right Side ===
        title = f"Enquiry Source Tracking\n{month_name} {year}"
        title_cell = ws.cell(row=start_row, column=7, value=title)
        title_cell.font = Font(name="Calibri", size=18, bold=True, color="1F4E79")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells(f"G{start_row}:I{start_row+1}")
        ws.row_dimensions[start_row].height = 50

        # === 3. Table Starts Here ===
        table_row = start_row + 3

        # Perfect column widths (matches your logo width exactly)
        column_settings = [
            ('A', 10),   # Sl No
            ('B', 25),   # Student Name
            ('C', 32),   # Course Name
            ('D', 18),   # Source
            ('E', 18),   # Enquiry Date
        ]
        for col, width in column_settings:
            ws.column_dimensions[col].width = width

        # Table Headers
        headers = ["Sl No", "Student Name", "Course Name", "Source", "Enquiry Date"]
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = None  # We'll use default blue later if needed
        thin_border = Border(left=Side("thin"), right=Side("thin"), top=Side("thin"), bottom=Side("thin"))

        # Write headers with blue background
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=table_row, column=col_num, value=header)
            cell.font = header_font
            cell.fill = PatternFill("solid", fgColor="1F4E79")  # Deep blue
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # Write data rows
        current_row = table_row + 1
        for idx, enq in enumerate(enquiries, start=1):
            course = enq.course_interested.course_name if enq.course_interested else "—"
            source = enq.get_heard_from_display()

            row_data = [idx, enq.student_name, course, source, enq.enquiry_date.strftime("%d/%m/%Y")]

            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=current_row, column=col_num, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")
                if col_num in [1, 5]:  # Sl No & Date
                    cell.alignment = Alignment(horizontal="center", vertical="center")

            current_row += 1

        # Make all data rows same height
        for r in range(table_row, current_row):
            ws.row_dimensions[r].height = 24

        # === Final: Return Excel File ===
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"Enquiry_Source_Tracking_{month_name}_{year}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response
    
class ExportEnquirySourceExcel(APIView):
    permission_classes = [AllowAny]  # or your auth

    def post(self, request, *args, **kwargs):
        header_image = request.FILES.get("header_image")

        today = date.today()
        enquiries = EnquiryArchive.objects.filter(
            enquiry_date__year=today.year,
            enquiry_date__month=today.month
        ).order_by('enquiry_date')

        wb = Workbook()
        ws = wb.active
        ws.title = "Source Tracking"

        headers = ["Sl No", "Student Name", "Course Name", "Source", "Enquiry Date"]
        column_widths = [10, 30, 35, 20, 18]

        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        start_row = 1

        # Header Image
        if header_image:
            try:
                img = XLImage(header_image)
                img.width = 680
                img.height = 140
                ws.row_dimensions[1].height = 105
                ws.add_image(img, "A1")
                start_row = 6
            except Exception as e:
                return HttpResponse(f"Image error: {e}", status=400)

        # Header Style
        table_row = start_row
        header_fill = PatternFill("solid", fgColor="1F4E79")
        header_font = Font(bold=True, color="FFFFFF")
        border = Border(left=Side("thin"), right=Side("thin"), top=Side("thin"), bottom=Side("thin"))

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=table_row, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        # DATA ROWS – FIXED SOURCE DISPLAY
        current_row = table_row + 1

        # SAFE CHOICES DICTIONARY (Never crashes)
        HEARD_FROM_CHOICES = {
            'walk in': 'Walk-in',
            'call': 'Call',
            'referral': 'Referral',
            'social media': 'Social Media',
            'website': 'Website',
        }

        for idx, enq in enumerate(enquiries, start=1):
            course = enq.course_interested or "Not Selected"
            source = HEARD_FROM_CHOICES.get(enq.heard_from, enq.heard_from or "Unknown")

            row_data = [
                idx,
                enq.student_name,
                course,
                source,
                enq.enquiry_date.strftime("%d/%m/%Y")
            ]

            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=current_row, column=col_num, value=value)
                cell.border = border
                cell.alignment = Alignment(vertical="center")
                if col_num in [1, 5]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

            current_row += 1

        # Row heights
        for r in range(table_row, current_row):
            ws.row_dimensions[r].height = 26

        # Return Excel
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        month_name = calendar.month_name[today.month]
        filename = f"Enquiry_Source_Tracking_{month_name}_{today.year}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response



class PaymentCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, admission_id=None):
        admission = get_object_or_404(Admission, id=admission_id, is_deleted=False)
        amount_paid_now = admission.admission_fee or Decimal('500.00')

        serializer = PaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Create payment
        payment = serializer.save(
            admission=admission,
            amount_paid_now=amount_paid_now
        )

        # Generate student_code ONLY if it's still blank
        if not admission.student_code:
            now = timezone.now()
            year_month = now.strftime("%b%Y").upper()  # NOV2025

            # Get course name safely
            course_name = "Unknown Course"
            if admission.course:
                course_name = admission.course.course_name
            elif admission.enquiry and admission.enquiry.course_interested:
                course_name = admission.enquiry.course_interested.course_name

            course_code = Admission.get_course_code(course_name)

            # This prevents duplicates even if multiple payments happen at once
            base_count = Admission.objects.filter(
                admission_date__year=now.year,
                admission_date__month=now.month,
                student_code__isnull=False
            ).count()

            sequence = base_count + 1

            admission.student_code = f"TS-EKM-GST-{course_code}-{year_month}-{sequence:04d}"
            admission.save(update_fields=['student_code'])

        # Update total fee_paid
        admission.fee_paid += amount_paid_now
        admission.save(update_fields=['fee_paid'])

       
        return Response({
            "payment_id": payment.id,
            "student_name": admission.enquiry.student_name if admission.enquiry else "Unknown",
            "receipt_number": payment.receipt_number,
            "student_code": admission.student_code,
            "payment_structure": payment.payment_structure,
            "payment_mode": payment.get_payment_mode_display(),
            "transaction_id": payment.transaction_id or "N/A",
            "course_name": admission.course.course_name if admission.course else "Not Selected",
            "admission_fee": f"{amount_paid_now:.2f}",
            "remarks": payment.remarks or "",
            "receipt_type": payment.get_receipt_type_display(),
        }, status=201)


from django.shortcuts import get_object_or_404
class ReceiptDataView(APIView):
    def get(self, request, pk):
        payment = get_object_or_404(Payment, id=pk)
        admission = payment.admission
        enquiry = admission.enquiry if admission and admission.enquiry else None
        receipt_type = payment.get_receipt_type_display()

        if not enquiry:
            return Response({"error": "Student enquiry not found"}, status=404)

        admission_fee = float(admission.admission_fee) if admission.admission_fee else 0.00
        amount_paid = float(payment.total_fee_amount)

        transaction_id = "N/A"
        if payment.payment_mode != "cash" and payment.transaction_id:
            transaction_id = payment.transaction_id

        data = {
            "student_name": enquiry.student_name or "N/A",
            "student_code": admission.student_code or "Not Generated Yet",
            "course_name": admission.course.course_name if admission.course else "Not Assigned",
            "receipt_number": payment.receipt_number,
            "current_date": timezone.now().strftime("%d/%m/%Y"),
            "payment_mode": payment.get_payment_mode_display(),
            "transaction_id": transaction_id,
            "admission_fee": admission_fee,
            # "total_fee": amount_paid + admission_fee + (float(admission.nactet_fee) if admission.nactet_fee else 0),
            "total_fee": amount_paid +(float(admission.nactet_fee) if admission.nactet_fee else 0),
            "remarks": payment.remarks or "",
            "receipt_type": payment.get_receipt_type_display(),
      
        }

        return Response(data)
    
from django.core.mail import EmailMessage

class SendReceiptEmail(APIView):
  
    def post(self, request, pk):
        # 1. Get Payment using pk from URL
        payment = get_object_or_404(
            Payment.objects.select_related('admission__enquiry'),
            id=pk
        )
        admission = payment.admission
        enquiry = admission.enquiry

        if not enquiry or not enquiry.email:
            return Response({
                "error": "Student email not found. Please add email in enquiry."
            }, status=400)

        student_name = enquiry.student_name
        student_email = enquiry.email
        receipt_number = payment.receipt_number

        # 2. Get the uploaded PDF from React
        pdf_file = request.FILES.get('receipt')
        if not pdf_file:
            return Response({"error": "PDF file is required (key: 'receipt')"}, status=400)

        # 3. Set clean filename
        filename = f"Receipt_{receipt_number}_{student_name.replace(' ', '_')}.pdf"

        # 4. Email content
        subject = f"Payment Receipt - {receipt_number}"
        message = f"""
Dear {student_name},

Thank you for your payment!

Please find your official payment receipt attached.

Receipt Number : {receipt_number}
Date           : {timezone.now().strftime("%d %B %Y")}

If you have any questions, feel free to contact us.

Best Regards,  
Techno Solutions Team  
Kochi, Kerala  
+91-XXXXXXXXXX | info@technosolutions.in
        """.strip()

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email="sysolmachinetest@gmail.com",
            to=[student_email],
        )
        email.attach(filename, pdf_file.read(), 'application/pdf')

        try:
            email.send(fail_silently=False)
            return Response({
                "success": True,
                "message": f"Receipt emailed successfully to {student_email}",
                "student_name": student_name,
                "receipt_number": receipt_number,
                "sent_to": student_email
            }, status=200)
        except Exception as e:
            return Response({
                "error": "Failed to send email",
                "details": str(e)
            }, status=500)



class PaidAdmissionsListView(APIView):
   

    def get(self, request):
        paid_admissions = Admission.objects.filter(
            is_deleted=False,payments__isnull=False,
            status__in=['pending', 'under review', 'under screening'],
            fee_paid__gt=0  
        ).select_related('enquiry', 'course').order_by('-id')
    
        serializer = PaidAdmissionListSerializer(paid_admissions, many=True)
        return Response({
            "count": paid_admissions.count(),
            "results": serializer.data
        })


class PaidAdmissionsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Admission.objects.filter(is_deleted=False).select_related('enquiry', 'course')
    serializer_class = PaidAdmissionDetailSerializer  

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PaidAdmissionUpdateSerializer
        return PaidAdmissionDetailSerializer

    def get_queryset(self):
        # Only allow paid admissions
        return Admission.objects.filter(is_deleted=False, payments__isnull=False)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full details after update
        return Response(PaidAdmissionDetailSerializer(instance, context={'request': request}).data)


class PaidAdmissionUpdateView(generics.UpdateAPIView):
    queryset = Admission.objects.filter(is_deleted=False)
    serializer_class = PaidAdmissionUpdateSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]  

    def get_queryset(self):
        return Admission.objects.filter(is_deleted=False, fee_paid__gt=0)

    def get_serializer_context(self):
        return {'request': self.request}

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

# DELETE multiple paid admissions 
class PaidAdmissionDeleteView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return Response({"error": "'ids' must be a list of integers"}, status=400)

        admissions = Admission.objects.filter(id__in=ids, is_deleted=False, payments__isnull=False)
        deleted_count = admissions.update(is_deleted=True)

        return Response({
            "status": "Success",
            "message": f"{deleted_count} paid admission(s) deleted."
        }, status=200)

# 1. LIST Confirmed Admissions
class ConfirmedAdmissionsListView(generics.ListAPIView):
    serializer_class = PaidAdmissionDetailSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Admission.objects.filter(
            is_deleted=False,
            status='confirmed' 
        ).select_related('enquiry', 'course') \
         .prefetch_related('payments') \
         .order_by('-admission_date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({
            "count": queryset.count(),
            "results": serializer.data
        })




class ConfirmAdmissionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, id):
        admission = get_object_or_404(
            Admission,
            id=id,
            is_deleted=False,
            payments__isnull=False
        )

        admission.status = 'confirmed'  # ← Must match your model choice: 'confirmed'
        admission.save(update_fields=['status'])

        serializer = PaidAdmissionDetailSerializer(admission, context={'request': request})

        return Response({
            "message": "Admission confirmed successfully!",
            "status": "confirmed",
            "admission": serializer.data
        }, status=status.HTTP_200_OK)
        
        



#graphical representation of seleted courses in each admisssions
from django.db.models import F, Count


from calendar import month_name

class CourseAdmissionStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = date.today()

        # Optional: allow ?month=11&year=2025
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if month and year:
            try:
                month,int(month), int(year)
                if not (1 <= month <= 12):
                    raise ValueError
            except ValueError:
                return Response({"error": "Invalid month/year"}, status=400)
        else:
            month = today.month
            year = today.year

        # Get all courses
        all_courses = course.objects.all().order_by('course_name')

        # Count ONLY CONFIRMED admissions
        admission_counts = Admission.objects.filter(
            admission_date__month=month,
            admission_date__year=year,
            is_deleted=False,
            status='confirmed'                    # ONLY THIS LINE CHANGED
        ).values('course__course_name') \
         .annotate(count=Count('id'))

        count_dict = {item['course__course_name']: item['count'] for item in admission_counts}

        courses_data = []
        for crs in all_courses:
            courses_data.append({
                "course_name": crs.course_name,
                "course_code": Admission.get_course_code(crs.course_name),
                "count": count_dict.get(crs.course_name, 0)  # 0 if no confirmed admission
            })

        return Response({
            "month": month,
            "year": year,
            "month_name": month_name[month],
            "courses": courses_data
        })

# # ==========================

# course, created = course.objects.get_or_create(
#     course_name="Data Science",
#     defaults={
#         'course_fee': 45000.00,
#         'duration_months': 6
#     }
# )
# # Now `course` is a real instance, not the class

# print(f"Course ready: {course.course_name} (created={created})")

# # Clear old test data (optional, safe)
# Enquiry.objects.filter(student_name__icontains="Test Student").delete()
# Admission.objects.filter(enquiry__student_name__icontains="Test Student").delete()

# # # Helper to create enquiry N months back
# def create_past_enquiry(months_back, name_prefix="Test Student"):
#     target_date = date.today() - timedelta(days=30*months_back)
#     return Enquiry.objects.create(
#         student_name=f"{name_prefix} {months_back}M Ago",
#         phone1="9999999999",
#         educational_qualification="B.Tech",
#         enquiry_date=target_date,
#         course_interested=course,
#         heard_from='walk in'
#     )

# # # Helper to create admission from enquiry
# def convert_to_admission(enquiry, days_after_enquiry=3):
#     admission_date = enquiry.enquiry_date + timedelta(days=days_after_enquiry)
#     return Admission.objects.create(
#         enquiry=enquiry,
#         course=course,
#         admission_date=admission_date,
#         status='confirmed'
#     )

# # # === CREATE DATA FOR LAST 3 MONTHS ===

# # # November 2025 (previous month if today is Dec 2025)
# for i in range(1, 21):  # 20 enquiries in Nov
#     enquiry = create_past_enquiry(months_back=1, name_prefix=f"Nov Student {i}")
#     if i <= 12:  # 12 out of 20 converted → 60% conversion
#         convert_to_admission(enquiry, days_after_enquiry=2)

# # # October 2025 (2 months back)
# for i in range(1, 16):  # 15 enquiries
#     enquiry = create_past_enquiry(months_back=2, name_prefix=f"Oct Student {i}")
#     if i <= 6:  # 6 converted → 40%
#         convert_to_admission(enquiry, days_after_enquiry=4)

# # # September 2025 (3 months back)
# for i in range(1, 25):
#     enquiry = create_past_enquiry(months_back=3, name_prefix=f"Sep Student {i}")
#     if i <= 18:  # 18 converted → 72%
#         convert_to_admission(enquiry, days_after_enquiry=1)

# print("Demo data created successfully for previous months!")















































