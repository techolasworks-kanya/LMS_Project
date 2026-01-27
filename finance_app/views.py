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
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from dotenv import load_dotenv
import os
import razorpay  # pyright: ignore[reportMissingImports]
from django.utils import timezone

# Initialize Razorpay client (ensure your .env has RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
load_dotenv()
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET else None


class GetDataForFeeCollection(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Only students who paid admission fee >= 500
        paid_admissions = Payment.objects.filter(
            admission_fee__gte=500
        ).select_related(
            'admission__enquiry',
            'admission__course'
        ).order_by('-payment_date')

        serializer = DataForFinanceSerializer(paid_admissions, many=True)

        return Response({
            'data': serializer.data,
            'message': 'Students eligible for course fee payment (admission fee ≥ ₹500)',
            'count': paid_admissions.count()
        }, status=status.HTTP_200_OK)

from django.db.models import Sum

from django.conf import settings
razorpay_client = settings.RAZORPAY_CLIENT
#===========================================
# UPDATED views.py - Add Razorpay Integration
# ============================================

class CreateFeeCollectionView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = FeeCollectionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'errors': serializer.errors,
                'message': 'Validation failed'
            }, status=status.HTTP_400_BAD_REQUEST)

        payment = serializer.validated_data['payment']
        admission = payment.admission
        payment_structure = serializer.validated_data.get('payment_structure')
        payment_mode = serializer.validated_data.get('payment_mode', 'cash')

        # Minimum admission fee check
        if payment.admission_fee < Decimal('500.00'):
            return Response({
                'message': 'Student has not paid sufficient admission fee (minimum ₹500 required)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # One-time payment: prevent overpayment
        if payment_structure == 'One time':
            existing = Fee_Collection.objects.filter(payment=payment)
            if existing.exists():
                paid_so_far = existing.aggregate(total=Sum('installment_amount'))['total'] or Decimal('0.00')
                base_total = serializer.validated_data['total_fee_amount']
                nactet_fee = Decimal('1000.00') if admission.interested_in_nactet == 'yes' else Decimal('0.00')
                total_with_nactet = base_total + nactet_fee
                discount = Decimal('5000.00') if serializer.validated_data.get('elegible_for_discount') == 'yes' else Decimal('0.00')
                final_total = total_with_nactet - discount

                if paid_so_far >= final_total:
                    return Response({
                        'message': 'One-time payment already fully paid.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if serializer.validated_data['payable_amount'] > (final_total - paid_so_far):
                    return Response({
                        'message': 'Payable amount exceeds remaining balance.'
                    }, status=status.HTTP_400_BAD_REQUEST)

        # Update NACTET interest
        new_nactet = serializer.validated_data.pop('interested_in_nactet', None)
        if new_nactet is not None:
            admission.interested_in_nactet = new_nactet
            admission.save(update_fields=['interested_in_nactet'])

        # Calculate totals
        base_total = serializer.validated_data['total_fee_amount']
        nactet_fee = Decimal('1000.00') if admission.interested_in_nactet == 'yes' else Decimal('0.00')
        total_fee = base_total + nactet_fee
        discounted_amount = total_fee - (Decimal('5000.00') if payment_structure == 'One time' and serializer.validated_data.get('elegible_for_discount') == 'yes' else Decimal('0.00'))

        previous_paid = Fee_Collection.objects.filter(payment=payment).aggregate(
            total=Sum('installment_amount')
        )['total'] or Decimal('0.00')

        payable_now = serializer.validated_data.pop('payable_amount')
        remaining_balance = discounted_amount - (previous_paid + payable_now)

        # Create fee collection
        fee_collection = serializer.save(
            payment=payment,
            total_fee_amount=discounted_amount,
            total_fee_paid=previous_paid,
            installment_amount=payable_now,
            payment_mode=payment_mode,
            payment_status='pending' if payment_mode in ['upi', 'card', 'bank transfer', ] else 'completed',
        )

        # Generate Razorpay Payment Link for online modes (works perfectly in Test Mode)
        payment_link_url = None
        razorpay_link_id = None

        if payment_mode in ['upi', 'card', 'bank transfer']:
            if razorpay_client is None:
                return Response({
                    'message': 'Razorpay not configured.',
                    'error': 'razorpay_not_available'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            try:
                link_data = {
                    "amount": int(payable_now * 100),  # paise
                    "currency": "INR",
                    "description": f"Fee Payment - {admission.course.course_name}",
                    "expire_by": int((timezone.now() + timezone.timedelta(hours=24)).timestamp()),
                    "customer": {
                        "name": admission.enquiry.student_name,
                        "contact": admission.enquiry.phone1,
                    },
                    "notify": {"sms": True, "email": True},
                    "reminder_enable": True,
                    "notes": {
                        "fee_collection_id": str(fee_collection.id),
                        "student_code": admission.student_code,
                        "purpose": "Course fee"
                    }
                }

                response = razorpay_client.payment_link.create(link_data)
                payment_link_url = response['short_url']
                razorpay_link_id = response['id']

                # Reuse razorpay_qr_id field to store payment link ID
                fee_collection.razorpay_qr_id = razorpay_link_id
                fee_collection.save(update_fields=['razorpay_qr_id'])

            except Exception as e:
                return Response({
                    'message': f'Error generating payment link: {str(e)}',
                    'error': 'razorpay_error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Response
        response_serializer = FeeCollectionCreateSerializer(fee_collection)
        data = response_serializer.data

        data.update({
            'payment_mode': payment_mode,
            'discounted_amount': float(discounted_amount),
            'remaining_balance': max(float(remaining_balance), 0.0),
            'previous_paid': float(previous_paid),
            'nactet_fee': float(nactet_fee),
            'payable_amount': float(payable_now),
            'payment_status': fee_collection.payment_status,
        })

        if payment_link_url:
            data.update({
                'payment_link_url': payment_link_url,
                'razorpay_reference_id': razorpay_link_id,
                'message': 'Payment link generated successfully. Share with student to complete payment.',
                'payment_instruction': 'Open the link and pay using UPI, Card, or Netbanking. Use test UPI ID: success@razorpay'
            })
        else:
            data['message'] = 'Fee collection recorded successfully (offline payment).'

        if remaining_balance <= 0 and payment_mode not in ['upi', 'card', 'bank transfer']:
            data.update({
                'payment_status': 'Fully Paid',
                'message': 'Full payment completed successfully.'
            })

        return Response(data, status=status.HTTP_201_CREATED)








