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
                .filter(follow_up_actions__isnull=True, admissions__isnull=True)
                .select_related('course_interested')
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

    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_superuser or (user.job_title and user.job_title.lower() == "admin"):
    #         return Enquiry.objects.all()
    #     return Enquiry.objects.none()

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

    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop('partial', True)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     followup = serializer.save()

    #     # === CRITICAL FIX: Fully refresh enquiry and course_interested from DB ===
    #     from django.db import connection
    #     connection.close()  # Optional: ensure no stale connection

    #     followup.enquiry = Enquiry.objects.select_related('course_interested').get(pk=followup.enquiry.pk)

    #     output = FollowUpListSerializer(followup, context=self.get_serializer_context()).data

    #     return Response({
    #         "status": "Follow-up updated successfully",
    #         "data": output
    #     })
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

        # --- ADD NEW REMARKS ---
        remarks = validated_data.pop('remarks', [])
        for content in remarks:
            if content.strip():
                FollowUpRemark.objects.create(followup=instance, content=content.strip())

        # --- RELOAD UPDATED FOLLOW-UP WITH REMARKS & ENQUIRY ---
        followup = FollowUps.objects.prefetch_related('remarks').get(pk=instance.pk)
        followup.enquiry = Enquiry.objects.select_related('course_interested').get(pk=followup.enquiry.pk)

        # --- RETURN SUCCESS RESPONSE ---
        output = FollowUpListSerializer(followup, context=self.get_serializer_context()).data

        return Response({
            "status": "Follow-up updated successfully",
            "data": output
        }, status=status.HTTP_200_OK)

        # if followup.status == 'interested':
        #     enquiry = followup.enquiry

        #     # Only create Admission if not already existing
        #     if not Admission.objects.filter(enquiry=enquiry).exists():
        #         Admission.objects.create(
        #             enquiry=enquiry,
        #             course=enquiry.course_interested,
        #             fee_paid=0.00,
        #             status='pending'
        #         )

        #     followup.delete()

        #     return Response({
        #         "status": "Follow-up marked as 'interested' and moved to Admissions successfully."
        #     }, status=status.HTTP_200_OK)

        # elif instance.status == "not_interested":
        #     NotInterestedLead.objects.create(
        #         followup=instance,
        #         enquiry=instance.enquiry,
        #         last_followup_date=instance.followup_date,
        #         status="not_interested",
        #         archived_on=timezone.now(),
        #     )
        #     instance.delete()  # Delete FollowUp

        #     return Response({
        #         "status": "Follow-up marked as 'not interested' and moved to Not Interested Leads successfully."
        #     }, status=status.HTTP_200_OK)
        
    
    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()      # the FollowUp
    #     self.perform_destroy(instance)    # deletes FollowUp → CASCADE deletes Enquiry
    #     return Response(
    #         {"status": "Follow-up and related enquiry deleted successfully."},
    #         status=status.HTTP_204_NO_CONTENT
    #     )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()        # the FollowUp
        self.perform_destroy(instance)      # ← deletes FollowUp → CASCADE deletes Enquiry
        return Response(
            {"status": "Follow-up and enquiry deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
    



# Admission
class AdmissionListCreateView(generics.ListCreateAPIView):
    queryset = Admission.objects.select_related('enquiry', 'enquiry__course_interested')
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

            self.created_admissions = created_admissions
            return

    # ---------------------------------------------------
    # 2) OLD LOGIC: ENQUIRIES → ADMISSIONS
    # ---------------------------------------------------
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

        # enquiry_ids = serializer.validated_data.pop('enquiry_ids')

        # # Validate enquiries
        # enquiries = Enquiry.objects.filter(
        #     id__in=enquiry_ids,
        #     follow_up_actions__isnull=True,
        #     admissions__isnull=True
        # )
        # found_ids = enquiries.values_list('id', flat=True)
        # missing = set(enquiry_ids) - set(found_ids)
        # if missing:
        #     raise serializers.ValidationError({
        #         "enquiry_ids": f"Enquiries {list(missing)} not found or already converted."
        #     })

        # created_admissions = []
        # for enquiry in enquiries:
        #     admission = Admission.objects.create(
        #         enquiry=enquiry,
        #         course=enquiry.course_interested,
        #         fee_paid=0.00,           # Default
        #         status='pending'         # Default
        #     )
        #     created_admissions.append(admission)

        # # DELETE enquiries
        # enquiries.delete()

        # # Store for response
        # self.created_admissions = created_admissions

        # Store for response

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




# class NotInterestedLeadCreateView(generics.CreateAPIView):
#     def create(self, request, *args, **kwargs):
#         followup_id = request.data.get('followup_id')
#         status = request.data.get('status', 'not_interested')

#         try:
#             followup = FollowUps.objects.select_related('enquiry').get(id=followup_id)
#         except FollowUps.DoesNotExist:
#             return Response({"error": "Follow-up not found"}, status=404)

#         if NotInterestedLead.objects.filter(followup=followup).exists():
#             return Response({"error": "Already archived"}, status=400)

#         NotInterestedLead.objects.create(
#             followup=followup,
#             enquiry=followup.enquiry,
#             last_followup_date=followup.followup_date,
#             status=status,
#             email=followup.enquiry.email
#         )
#         followup.delete()

#         return Response({
#             "status": "Moved to Not Interested",
#             "student_name": followup.enquiry.student_name
#         }, status=201)
class NotInterestedLeadCreateView(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        followup_ids = request.data.get('followup_ids', None)

        if not followup_ids:
            return Response(
                {"error": "'followup_ids' is required"},
                status=400
            )

        # Ensure list type
        if not isinstance(followup_ids, list):
            return Response(
                {"error": "'followup_ids' must be a list of integers"},
                status=400
            )

        followups = FollowUps.objects.select_related('enquiry').filter(id__in=followup_ids)

        if followups.count() != len(followup_ids):
            return Response(
                {"error": "One or more followups not found"},
                status=404
            )

        created_records = []

        for followup in followups:

            # ------------------------------------------------------
            # ❗ MUST BE NOT_INTERESTED — same logic as admissions
            # ------------------------------------------------------
            if followup.status != "not_interested":
                return Response(
                    {"error": f"Follow-up {followup.id} is not marked as 'not_interested'"},
                    status=400
                )

            # Prevent duplicate archive
            if NotInterestedLead.objects.filter(followup=followup).exists():
                return Response(
                    {"error": f"Follow-up {followup.id} already archived"},
                    status=400
                )

            record = NotInterestedLead.objects.create(
                followup=followup,
                enquiry=followup.enquiry,
                last_followup_date=followup.followup_date,
                status="not_interested"
            )

            created_records.append(record)

            # delete followup from table
            followup.delete()

        return Response({
            "status": f"{len(created_records)} followup(s) moved to Not Interested",
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
# CREATE
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


# UNREAD ONLY (filtered by module)
class NotificationUnreadListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        module = self.request.query_params.get('module')
        queryset = Notification.objects.filter(is_read=False)
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