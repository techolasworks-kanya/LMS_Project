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

    def get_serializer_class(self):
        return EnquiryCreateSerializer if self.request.method == 'POST' else EnquiryListSerializer

    # def get_queryset(self):
    #     if self.request.method == 'GET':
    #         return Enquiry.objects.exclude(
    #             admissions__isnull=False  
                
    #         ).select_related('course_interested').order_by('-id')
        
    #     return super().get_queryset()
    def get_queryset(self):
        if self.request.method == 'GET':
            return Enquiry.objects.exclude(
                admissions__isnull=False
            ).exclude(
                is_archived=True                     
            ).select_related('course_interested').order_by('-id')
        
        return super().get_queryset()


    def perform_create(self, serializer):
        return serializer.save()  

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enquiry = self.perform_create(serializer)

        # Use the same serializer for response
        response_data = {
            "student_name": enquiry.student_name,
            "heard_from": enquiry.heard_from,
            "date_of_birth": enquiry.date_of_birth,
            "course_interested": (
                enquiry.course_interested.course_name
                if enquiry.course_interested else None
            ),
        }

        return Response({
            "status": "Enquiry created successfully",
            "data": response_data
        }, status=status.HTTP_201_CREATED)
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
    # queryset = FollowUps.objects.select_related('enquiry', 'enquiry__course_interested').prefetch_related('remarks')
    def get_queryset(self):
        if self.request.method == 'GET':
            return FollowUps.objects.select_related(
                'enquiry', 'enquiry__course_interested'
            ).prefetch_related('remarks').order_by('-id')
        return super().get_queryset()

    
    permission_classes = [AllowAny]
    # pagination_class = PageNumberPagination

    def get_serializer_class(self):
        return FollowUpListSerializer if self.request.method == 'GET' else FollowUpDetailSerializer

    def perform_create(self, serializer):
        enquiry_ids = serializer.validated_data.pop('enquiry_ids')
        remarks = serializer.validated_data.pop('remarks', [])

        # Validate enquiries exist and not already converted
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

        # DELETE enquiries
        # enquiries.delete()

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

        # # --- ADD NEW REMARKS ---
        # remarks = validated_data.pop('remarks', [])
        # for content in remarks:
        #     if content.strip():
        #         FollowUpRemark.objects.create(followup=instance, content=content.strip())

        

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

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        if month and year:
            queryset = queryset.filter(
                admission_date__month=month,
                admission_date__year=year
            )

        return queryset.order_by('-id')
    
    permission_classes = [AllowAny]
    # pagination_class = PageNumberPagination

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
                # enquiry.delete()

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

                # enquiry.delete()

            # enquiries.delete()
            self.created_admissions = created_admissions
            return

        # ---------------------------------------------------
        # NOTHING PROVIDED
        # ---------------------------------------------------
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
    queryset = Admission.objects.select_related('enquiry', 'enquiry__course_interested')
    serializer_class = AdmissionUpdateSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'


    def post(self, request, *args, **kwargs):
        # If no ID in URL → Manual Create
        if not kwargs.get('id'):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            admission = serializer.save()
            return Response({
                "status": "Manual admission created successfully!",
                "admission_id": admission.id,
                "student_code": admission.student_code,
                "message": "Go to payment now"
            }, status=201)

        # Otherwise → Normal Update (existing)
        return self.patch(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_deleted:
            return Response({"error": "Cancelled admission cannot be updated"}, status=400)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_admission = serializer.save()

        # Return FULL data using your existing ListSerializer
        full_data = AdmissionListSerializer(updated_admission).data
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

# ALL NOTIFICATIONS (filtered by module)
class NotificationAllListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        module = self.request.query_params.get('module')
        queryset = Notification.objects.all()
        if module:
            queryset = queryset.filter(module=module)
        return queryset




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


import calendar
# class ConversionStatsView(APIView):
#     def get(self, request):

#         # Get current date
#         today = date.today()
#         month = today.month
#         year = today.year

#         # Fetch data for current month automatically
#         enquiries = Enquiry.objects.filter(
#             enquiry_date__month=month, enquiry_date__year=year
#         )

#         admissions = Admission.objects.filter(
#             admission_date__month=month, admission_date__year=year
#         )

#         # Convert month number → month name
#         month_name = calendar.month_name[month]

#         data = {
#             "month": month_name,
#             "year": year,
#             "total_enquiries": enquiries.count(),
#             "total_admissions": admissions.count(),
#         }

#         serializer = ConversionStatsSerializer(data)
#         return Response(serializer.data)
class ConversionStatsView(APIView):
    def get(self, request):
        today = date.today()
        month = today.month
        year = today.year

        total_enquiries = Enquiry.objects.filter(
            enquiry_date__month=month,
            enquiry_date__year=year
        ).count()

        total_admissions = Admission.objects.filter(
            enquiry__enquiry_date__month=month,
            enquiry__enquiry_date__year=year
        ).count()

        month_name = calendar.month_name[month]

        if total_enquiries > 0:
            admission_rate = round((total_admissions / total_enquiries) * 100)
        else:
            admission_rate = 0

        data = {
            "month": month_name,
            "year": year,
            "total_enquiry": total_enquiries,
            "total_admission": total_admissions,
            "admission_rate": f"{admission_rate}%"
        }

        # Correct way: use data= keyword
        serializer = ConversionStatsSerializer(data=data)
        serializer.is_valid(raise_exception=True)  # optional but good practice
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
        # Get admission from URL
        admission = get_object_or_404(Admission, id=admission_id, is_deleted=False)

        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(admission=admission)

            # Update total fee_paid in admission
            admission.fee_paid += payment.amount
            admission.save()

            return Response({
                "status": "Payment recorded successfully!",
                "payment_id": payment.id,
                "receipt_number": payment.receipt_number,
                "student_name": payment.admission.enquiry.student_name if payment.admission.enquiry else "Student",
                "course_name": payment.admission.course.course_name if payment.admission.course else "N/A",
                "amount_paid": str(payment.amount + payment.admission_fee),
                "print_url": f"/receipt/print/{payment.id}/",
                "message": "Receipt ready to print"
            }, status=201)

        return Response(serializer.errors, status=400)


from django.shortcuts import get_object_or_404
class ReceiptPrintView(APIView):
    def get(self, request, pk):
        payment = get_object_or_404(Payment, id=pk)
        student = payment.admission.enquiry
        student_name = student.student_name if student else "Student"
        course_name = payment.admission.course.course_name if payment.admission.course else "N/A"

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Receipt - {payment.receipt_number}</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; margin: 40px; background: #f9f9f9; }}
                .receipt {{ 
                    max-width: 700px; margin: auto; border: 3px solid #003366; 
                    padding: 30px; background: white; box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{ background: #003366; color: white; padding: 20px; text-align: center; margin: -30px -30px 30px -30px; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .label {{ font-weight: bold; width: 180px; }}
                .amount-table {{ width: 100%; border: 2px solid #000; margin: 30px 0; }}
                .amount-table th, .amount-table td {{ padding: 12px; text-align: left; border: 1px solid #000; }}
                .amount-table th {{ background: #f0f0f0; }}
                .total-row {{ background: #e6f3ff !important; font-weight: bold; font-size: 18px; }}
                .footer {{ margin-top: 50px; text-align: center; color: #003366; }}
                .print-btn {{ 
                    background: #003366; color: white; padding: 15px 40px; 
                    font-size: 18px; border: none; border-radius: 8px; cursor: pointer; margin: 20px 10px;
                }}
                @media print {{
                    body {{ margin: 0; }}
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body onload="window.print()">
            <div class="receipt">
                <div class="header">
                    <h1>TECHOLAS TECHNOLOGIES</h1>
                    <p>techolas@gmail.com | 1234567890</p>
                </div>

                <table>
                    <tr>
                        <td class="label">Receipt No:</td>
                        <td><strong>{payment.receipt_number}</strong></td>
                        <td class="label">Date:</td>
                        <td><strong>{payment.payment_date.strftime('%d/%m/%Y')}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">Bill To :</td>
                        <td></td>
                        <td class="label">Payment Mode :</td>
                        <td><strong>{payment.get_payment_mode_display()}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">Student Name :</td>
                        <td><strong>{student_name}</strong></td>
                        <td class="label">Transaction ID :</td>
                        <td><strong>{payment.transaction_id or 'N/A'}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">Student ID :</td>
                        <td colspan="3"><strong>{payment.admission.student_code}</strong></td>
                    </tr>
                </table>

                <table class="amount-table">
                    <tr><th>Description</th><th>Amount</th></tr>
                    <tr>
                        <td>Course Name : {course_name}</td>
                        <td>₹{payment.amount}</td>
                    </tr>
                    {"<tr><td>Admission Fee</td><td>₹{}</td></tr>".format(payment.admission_fee) if payment.admission_fee > 0 else ""}
                    <tr class="total-row">
                        <td>Total Amount Paid</td>
                        <td>₹{payment.amount + payment.admission_fee}</td>
                    </tr>
                </table>

                <p><strong>Remarks:</strong> {payment.remarks or 'None'}</p>

                <div class="footer">
                    <h3>Thank you for your payment</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li>• This is computer generated and valid without signature</li>
                        <li>• No refund applicable unless explicitly mentioned</li>
                    </ul>
                </div>

                <div class="no-print" style="text-align: center; margin-top: 40px;">
                    <button class="print-btn" onclick="window.print()">Print Receipt</button>
                    <button class="print-btn" style="background: #666;" onclick="window.close()">Close</button>
                </div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)