from django.shortcuts import render
from LMS_app.models import *
from LMS_app.serializers import *
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from .serializers import *
from rest_framework.response import Response 
from rest_framework.views import APIView
# Create your views here.
class GetDataForFinance(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        paid_admissions = Payment.objects.filter(
            admission_fee__gt=0
        ).select_related(
            'admission__enquiry',
            'admission__course'
        ).order_by('-payment_date')

        serializer = DataForFinanceSerializer(paid_admissions, many=True)

        return Response({
            'data': serializer.data,
            'message': 'Students who have paid admission fee',
            'count': paid_admissions.count()
        })
