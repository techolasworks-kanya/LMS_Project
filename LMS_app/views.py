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
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import logout
from django.middleware import csrf

@api_view(['GET'])
def server_running(request):
    return Response({"message": "Server running"})


class UserLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)

        # Manually add CSRF token to response (so Postman can see it)
        csrf_token = csrf.get_token(request)

        return Response({
            "message": f"{'Superadmin' if user.is_superuser else user.job_title or 'User'} logged in successfully",
            "email": user.email,
            "job_title": user.job_title,
            "is_superuser": user.is_superuser,
            "csrf_token": csrf_token  # helpful for Postman testing
        }, status=status.HTTP_200_OK)


class UserLogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


class CreateUserAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # ✅ Only superadmin can create users/admins
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

# Enquiry
class EnquiryListCreateView(generics.ListCreateAPIView):
    queryset = Enquiry.objects.all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Allow anyone to create enquiries (optional)
        if self.request.method == 'POST':
            return []
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EnquiryCreateSerializer
        return EnquiryListSerializer

    def get_queryset(self):
        user = self.request.user
        # ✅ Only admins can view all enquiries
        if user.is_superuser or (user.job_title and user.job_title.lower() == "admin"):
            return Enquiry.objects.all()
        # ✅ Normal users can view their own enquiries (optional)
        return Enquiry.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"status": "Enquiry created successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class EnquiryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquiryCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # ✅ Admins and superadmin can view/edit/delete any enquiry
        if user.is_superuser or (user.job_title and user.job_title.lower() == "admin"):
            return Enquiry.objects.all()
        # ✅ Others have no access
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

