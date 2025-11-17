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
# from django.utils.decorators import method_decorator
from django.contrib.auth import logout
# from django.db.models import Q

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView  


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

class EnquiryListCreateView(generics.ListCreateAPIView):
    queryset = Enquiry.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        return EnquiryCreateSerializer if self.request.method == 'POST' else EnquiryListSerializer

    def get_queryset(self):
        if self.request.method == 'GET':
          
            return (
                Enquiry.objects
                .filter(
                    follow_up_actions__isnull=True,
                    admissions__isnull=True,
                    not_interested_records__isnull=True
                )
                .select_related('course_interested')
                .distinct()
                .order_by('-id')
            )
        return super().get_queryset()

    def perform_create(self, serializer):
        return serializer.save()  # <-- Return the created object

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
        enquiries.delete()

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


        # instance = self.get_object()        # the FollowUp
        # self.perform_destroy(instance)      # ← deletes FollowUp → CASCADE deletes Enquiry
        return Response(
            {"status": "Follow-up and enquiry deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        ) 



# Admission
class AdmissionListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        queryset = Admission.objects.select_related('enquiry', 'enquiry__course_interested')

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        if month and year:
            queryset = queryset.filter(
                admission_date__month=month,
                admission_date__year=year
            )

        return queryset
    permission_classes = [AllowAny]

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
                enquiry.delete()

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

            enquiries.delete()
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


#admission excel export view

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

            created_records.append(record)

             # 1️⃣ UPDATE ENQUIRY STATUS
            followup.enquiry.status = "not_interested"
            followup.enquiry.save()

            # NOW delete only followup (NOT enquiry)
            followup.delete()
            

        return Response({
            "status": "Success",
            "message": f"{len(created_records)} followup(s) moved to Not Interested",
            "data": [r.id for r in created_records]
        }, status=201)

# LIST with SEARCH
class NotInterestedLeadListView(generics.ListAPIView):
    serializer_class = NotInterestedLeadListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = NotInterestedLead.objects.select_related(
            'followup', 'enquiry', 'enquiry__course_interested'
        )
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                enquiry__student_name__icontains=search
            )
        return queryset
    

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
class ConversionStatsView(APIView):
    def get(self, request):

        # Get current date
        today = date.today()
        month = today.month
        year = today.year

        # Fetch data for current month automatically
        enquiries = Enquiry.objects.filter(
            enquiry_date__month=month, enquiry_date__year=year
        )

        admissions = Admission.objects.filter(
            admission_date__month=month, admission_date__year=year
        )

        # Convert month number → month name
        month_name = calendar.month_name[month]

        data = {
            "month": month_name,
            "year": year,
            "total_enquiries": enquiries.count(),
            "total_admissions": admissions.count(),
        }

        serializer = ConversionStatsSerializer(data)
        return Response(serializer.data)





from collections import Counter

class EnquirySourceStatsView(APIView):
    def get(self, request):

        # Auto-detect current month and year
        today = date.today()
        month = today.month
        year = today.year

        # Get all enquiries for the current month
        enquiries = Enquiry.objects.filter(
            enquiry_date__month=month,
            enquiry_date__year=year
        )

        # Count by source (heard_from)
        source_counts = Counter(enq.heard_from for enq in enquiries)

        # Total enquiries of the month
        total = sum(source_counts.values())

        # Compute percentage + count
        source_stats = {}
        for source, count in source_counts.items():
            percentage = round((count / total) * 100, 2) if total > 0 else 0
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



        






























































