from django.urls import path
from . import views
from LMS_app.views import *

urlpatterns = [
    path('api/get-data-for-finance', views.GetDataForFeeCollection.as_view(), name='finance-data'),
    path('api/create-fee-collection', views.CreateFeeCollectionView.as_view(), name='create-fee-collection'),

    # path('api/fee-collection-create', views.CreateFeeCollection.as_view(), name='create-fee-collection'),
    
]