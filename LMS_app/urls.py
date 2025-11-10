from django.urls import path
from . import views
from .views import server_running

urlpatterns = [

    path('', server_running, name='server-running'),

   

    path('api/courses', views.CourseListCreateView.as_view(), name='course-create-list'),
    path('api/courses/<int:pk>', views.CourseDetailView.as_view(), name='course-retrieve-update-destroy'),

    #certfication API endpoints
    path('api/certfications', views.CertficationListCreateView.as_view(), name='certfication-create-list'),


    #user creatons/regstration
    path('api/login', views.UserLoginView.as_view(), name='user-login'),
    path('api/reset-password', views.ResetPasswordView.as_view(), name='reset_password'),
    path('api/logout', views.UserLogoutView.as_view(), name='user-logout'),
    path('api/token/refresh', views.TokenRefreshView.as_view()),
    path('api/users_register', views.CreateUserAPIView.as_view(), name='user-register'),


 #enquiry API endpoints
    path('api/enquiries', views.EnquiryListCreateView.as_view(), name='enquiry-create-list'),
    path('api/enquiries/<int:pk>', views.EnquiryDetailView.as_view(), name='enquiry-retrieve-update-destroy'),


#folloup actions API endpoints
    path('api/followups', views.FollowUpListCreateView.as_view(), name='followup-list-create'),
    path('api/followups/<int:pk>', views.FollowUpDetailView.as_view(), name='followup-detail'),


# Admission API endpoints

    path('api/admissions', views.AdmissionListCreateView.as_view(), name='admission-list-create'),
    path('api/admissions/<int:pk>', views.AdmissionDetailView.as_view(), name='admission-detail'),

#not interested leads API endpoints
path('api/not-interested', views.NotInterestedLeadListView.as_view(), name='not-interested-list'),
path('api/not-interested/create', views.NotInterestedLeadCreateView.as_view(), name='not-interested-create'),



]