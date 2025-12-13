from django.urls import path
from . import views
from LMS_app.views import *

urlpatterns = [
    path('api/get-data-for-finance', views.GetDataForFinance.as_view(), name='finance-data'),
]