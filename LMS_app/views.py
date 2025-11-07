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

# class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = course.objects.all()
#     serializer_class = CourseCreateSerializer
#     def update(self, request, *args, **kwargs):
#         response = super().update(request, *args, **kwargs)
#         response.data = {
#             "status": "Course updated successfully.",
#             "data": response.data
#         }
#         return response


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

    def get_permissions(self):
        if self.request.method == 'POST':
            return []  # Anyone can create
        return [AllowAny()]  # Anyone can view

    def get_serializer_class(self):
        return EnquiryCreateSerializer if self.request.method == 'POST' else EnquiryListSerializer

    def get_queryset(self):
        # SHOW ALL ENQUIRIES TO EVERYONE
        return Enquiry.objects.all().order_by('-enquiry_date')

    def perform_create(self, serializer):
        # No created_by → just save
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"status": "Enquiry created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )

# class EnquiryListCreateView(generics.ListCreateAPIView):
#     queryset = Enquiry.objects.all()
#     permission_classes = [AllowAny]  

#     def get_permissions(self):
#         if self.request.method == 'POST':
#             return []  # Anyone can create
#         return [AllowAny()]  # GET: anyone can view

#     def get_serializer_class(self):
#         return EnquiryCreateSerializer if self.request.method == 'POST' else EnquiryListSerializer

#     def get_queryset(self):
#         # SHOW ALL ENQUIRIES — NO FILTER
#         return Enquiry.objects.all().order_by('-enquiry_date')

#     # def perform_create(self, serializer):
#     #     # Optional: still save created_by if logged in
#     #     if self.request.user.is_authenticated:
#     #         serializer.save(created_by=self.request.user)
#     #     else:
#     #         email = serializer.validated_data.get('email')
#     #         try:
#     #             user = CustomUser.objects.get(email__iexact=email)
#     #             serializer.save(created_by=user)
#     #         except CustomUser.DoesNotExist:
#     #             serializer.save(created_by=None)
#     def perform_create(self, serializer):
#     # If user is logged in → attach them
#         if self.request.user.is_authenticated:
#             serializer.save(created_by=self.request.user)
#         else:
#             # Try to link enquiry to existing user by email
#             email = serializer.validated_data.get('email')
#             if email:
#                 try:
#                     user = CustomUser.objects.get(email__iexact=email)
#                     serializer.save(created_by=user)
#                 except CustomUser.DoesNotExist:
#                     # User doesn't exist → save without created_by
#                     serializer.save(created_by=None)
#             else:
#                 # No email provided → save anonymously
#                 serializer.save(created_by=None)

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         return Response(
#             {"status": "Enquiry created successfully", "data": serializer.data},
#             status=status.HTTP_201_CREATED
#         )


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

