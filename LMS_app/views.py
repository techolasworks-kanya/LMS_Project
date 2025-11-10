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
        if self.request.method == 'POST':
            return EnquiryCreateSerializer
        return EnquiryListSerializer  # For GET

    def get_queryset(self):
        if self.request.method == 'GET':
            return (
                Enquiry.objects
                .filter(follow_up_actions__isnull=True)
                .select_related('course_interested')  # This is the fix
                .order_by('-id')
            )
        return super().get_queryset()

    def perform_create(self, serializer):
    # Extract raw input from validated data
        raw = serializer.validated_data.pop('_course_input', None)
        enquiry = serializer.save()
        enquiry._course_input = raw
        return enquiry

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enquiry = self.perform_create(serializer)

        # Use list serializer for output
        list_serializer = EnquiryListSerializer(enquiry)
        return Response(
            {
                "status": "Enquiry created successfully",
                "data": list_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
class EnquiryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquiryCreateSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (user.job_title and user.job_title.lower() == "admin"):
            return Enquiry.objects.all()
        return Enquiry.objects.none()

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



# class FollowUpListCreateView(generics.ListCreateAPIView):
#     queryset = FollowUps.objects.select_related(
#         'enquiry', 'enquiry__course_interested'
#     ).prefetch_related('remarks')
#     permission_classes = [AllowAny]  

#     def get_serializer_class(self):
#         if self.request.method == 'GET':
#             return FollowUpListSerializer
#         return FollowUpDetailSerializer

#     def perform_create(self, serializer):
#         # Auto-set enquiry_source on create
#         enquiry = serializer.validated_data['enquiry']
#         followup = serializer.save(enquiry_source=enquiry.heard_from)
        
#         # Add remark if provided
#         remarks = self.request.data.get('remarks', [])
#         for content in remarks:
#             if content.strip():
#                 FollowUpRemark.objects.create(followup=followup, content=content.strip())

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)
#         return Response(
#             {"status": "Follow-up created", "data": serializer.data},
#             status=status.HTTP_201_CREATED,
#             headers=headers
#         )

class FollowUpListCreateView(generics.ListCreateAPIView):
    queryset = FollowUps.objects.select_related(
        'enquiry', 'enquiry__course_interested'
    ).prefetch_related('remarks')
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        return FollowUpListSerializer if self.request.method == 'GET' else FollowUpDetailSerializer

    def perform_create(self, serializer):
        enquiry_ids = serializer.validated_data.pop('enquiry_ids')
        remarks = serializer.validated_data.pop('remarks', [])

    # Validate enquiries exist and not already converted
        enquiries = Enquiry.objects.filter(
            id__in=enquiry_ids,
            follow_up_actions__isnull=True
        )
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
                next_followup_date=serializer.validated_data.get('next_followup_date'),
            )

            if remarks:
                # Option: assign all remarks to each follow-up
                for content in remarks:
                    if content.strip():
                        FollowUpRemark.objects.create(followup=followup, content=content.strip())
              
            created_followups.append(followup)

        # DELETE all enquiries
        enquiries.delete()

    # Return first follow-up for response (or list all?)
        serializer.instance = created_followups[0] if created_followups else None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Serialize all created follow-ups
        followup_serializer = FollowUpListSerializer(
            serializer.instance, context={'request': request}
        ) if serializer.instance else None

        return Response({
            "status": f"{len(request.data.get('enquiry_ids', []))} follow-up(s) created successfully",
            "data": followup_serializer.data if followup_serializer else None
        }, status=status.HTTP_201_CREATED)
    
# class FollowUpDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = FollowUps.objects.select_related('enquiry', 'enquiry__course_interested').prefetch_related('remarks')
#     serializer_class = FollowUpDetailSerializer
#     permission_classes = [AllowAny]

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)

#         return Response({
#             "status": "Follow-up updated successfully",
#             "data": serializer.data
#         })
class FollowUpDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FollowUps.objects.select_related(
        'enquiry', 'enquiry__course_interested'
    ).prefetch_related('remarks')
    serializer_class = FollowUpDetailSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        followup = self.get_object()

        serializer = self.get_serializer(followup, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Extract remarks
        remarks = serializer.validated_data.pop('remarks', [])

        # Update FollowUp
        followup = serializer.save()

        # Update nested Enquiry
        enquiry_data = serializer.validated_data.pop('enquiry', {})
        if enquiry_data:
            enquiry_serializer = EnquiryNestedUpdateSerializer(
                followup.enquiry, data=enquiry_data, partial=True
            )
            enquiry_serializer.is_valid(raise_exception=True)
            enquiry_serializer.save()

        # Add new remarks
        for content in remarks:
            if content.strip():
                FollowUpRemark.objects.create(followup=followup, content=content.strip())

        # Return full updated data
        output = self.get_serializer(followup).data
        return Response({
            "status": "Follow-up and enquiry updated successfully",
            "data": output
        })