from django.urls import path
from . import views
from .views import server_running
from .views import ExportAdmissionExcel

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
    path('api/today-enquiries', views.TodayEnquiryListView.as_view(), name='today-enquiries'),
    path('api/enquiry-status-counts', views.EnquiryStatusListView.as_view(), name='enquiry-status-counts'),
    path('api/enquiries/export-excel', views.ExportEnquiryExcel.as_view(), name='export-enquiry-excel'),

    #facebook leads API endpoints
    # path('api/facebook-leads', views.FacebookLeadWebhookView.as_view(), name='facebook-lead-list-create'),
#folloup actions API endpoints
    path('api/followups', views.FollowUpListCreateView.as_view(), name='followup-list-create'),
    path('api/followups/<int:pk>', views.FollowUpDetailView.as_view(), name='followup-detail'),


# Admission API endpoints

    path('api/admissions', views.AdmissionListCreateView.as_view(), name='admission-list-create'),
    path('api/admissions/<int:pk>', views.AdmissionDetailView.as_view(), name='admission-detail'),
    path('api/admissions/update/<int:id>', views.AdmissionUpdateView.as_view(), name='admission-update'),
    path('api/admissions/delete-multiple', views.AdmissionDeleteView.as_view()),
    path('api/admissions/create_admissions', views.AdmissionUpdateView.as_view(), name='admission-manual-create'),
    path('api/admission_payment_info/<int:admission_id>', views.AdmissionPaymentInfoView.as_view(), name='payment-info'),
    path('api/monthly-enquiry-to-admission-converted-count', views.MonthlyEnquiryToAdmissionConversionView.as_view()),

#not interested leads API endpoints
    path('api/not-interested', views.NotInterestedLeadListView.as_view(), name='not-interested-list'),
    path('api/not-interested/create', views.NotInterestedLeadCreateView.as_view(), name='not-interested-create'),

# notifications API endpoints
    path('api/notifications/create', views.NotificationCreateView.as_view(), name='notification-create'),
    path('api/notifications/all', views.NotificationAllListView.as_view(), name='notification-all'),
    path('api/notifications/<int:pk>', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('api/updatenotification/<int:pk>', views.NotificationUpdateView.as_view(), name='notification-update'),
    path('api/notifications/admission', views.AdmissionNotificationListView.as_view(), name='admission-notifications'),


# chart endpoints
    path('api/conversion-stats', views.ConversionStatsView.as_view(), name='conversion_stats'),
    path('api/enquiry-source-stats', views.EnquirySourceStatsView.as_view(), name='enquiry_source_stats'),
    path("api/admissions/export-excel", ExportAdmissionExcel.as_view(),name="export-excel-dynamic"),
    path('export/enquiry-source-excel', views.ExportEnquirySourceExcel.as_view(), name='export-enquiry-source'),
#payment
    path('api/payment_create/<int:admission_id>', views.PaymentCreateView.as_view()),
    path('api/receipt_data/<int:pk>', views.ReceiptDataView.as_view(), name='receipt-print'),
    path('api/send-receipt/<int:pk>', views.SendReceiptEmail.as_view(), name='send-receipt-email'),

    path('api/paid-admissions', views.PaidAdmissionsListView.as_view(), name='paid-admissions'),
    path('api/paid-admissions/<int:pk>', views.PaidAdmissionsDetailView.as_view(), name='paid-admissions-detail'),
    path('api/paid-admissions/delete-multiple', views.PaidAdmissionDeleteView.as_view(), name='paid-admissions-delete-multiple'),
    path('api/confirmed-admissions', views.ConfirmedAdmissionsListView.as_view(), name='confirmed-list'),
    path('api/admissions/confirm/<int:id>', views.ConfirmAdmissionView.as_view(), name='admission-confirm'),


#graphical representation of seleted courses in each admisssions
    path('api/admissions/course-counts', views.CourseAdmissionStatsView.as_view()),



    



    

]


