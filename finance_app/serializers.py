from LMS_app.serializers import *
from LMS_app.models import *
from rest_framework import serializers
from .models import Fee_Collection
from decimal import Decimal

class DataForFinanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='admission.enquiry.student_name', read_only=True)
    course_name = serializers.CharField(source='admission.course.course_name', read_only=True)
    no_of_course_installments = serializers.IntegerField(source='admission.course.number_of_installments', read_only=True, allow_null=True)
    phone_number = serializers.CharField(source='admission.enquiry.phone1', read_only=True)
    student_code = serializers.CharField(source='admission.student_code', read_only=True)
   
    batch_id = serializers.IntegerField(read_only=True, allow_null=True)

    # New fields: NACTET status and fee from Admission
    interested_in_nactet = serializers.CharField(source='admission.interested_in_nactet',read_only=True,allow_null=True  )
    nactet_fee = serializers.DecimalField(source='admission.nactet_fee',max_digits=8,decimal_places=2,read_only=True,allow_null=True)

    class Meta:
        model = Payment
        fields = [
            'student_code',
            'student_name',
            'course_name',
            'no_of_course_installments',
            'phone_number',
            'total_fee_amount',
            'batch_id',
            'interested_in_nactet',   
            'nactet_fee',             
        ]


from decimal import Decimal
# Serializer for creating Fee_Collection



class FeeCollectionCreateSerializer(serializers.ModelSerializer):
    payment_id = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.all(),
        source='payment',
        write_only=True
    )
    interested_in_nactet = serializers.ChoiceField(
        choices=['yes', 'no'], required=False, write_only=True
    )
    payable_amount = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    payment_mode = serializers.ChoiceField(
        choices=['cash', 'upi', 'card', 'bank transfer'],
        write_only=True)
    # Read-only fields for response
    student_name = serializers.CharField(source='payment.admission.enquiry.student_name', read_only=True)
    course_name = serializers.CharField(source='payment.admission.course.course_name', read_only=True)
    student_code = serializers.CharField(source='payment.admission.student_code', read_only=True)
    phone_number = serializers.CharField(source='payment.admission.enquiry.phone1', read_only=True)

    discounted_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    qr_code_id = serializers.CharField(read_only=True)

    class Meta:
        model = Fee_Collection
        fields = [
            'id',
             # response only
            'student_name',
            'course_name',
            'student_code',
            'phone_number',
            #________________
            'payment_id',
            'payment_mode',
            'payment_structure',
            'elegible_for_discount',
            'discount_type',
            'webinar_application_timing',
            'no_of_refferal',
            'refferal_amount',
            'installment_number',
            'installment_amount',
            'total_fee_amount',
            'total_fee_paid',

            # editable NACTET
            'interested_in_nactet',

            # amount being paid now
            'payable_amount',

            # response only
            
            'discounted_amount',
            'remaining_balance',
            'qr_code_id',
           
        ]
        extra_kwargs = {
            'total_fee_paid': {'read_only': True},
            'discounted_amount': {'read_only': True},
            'remaining_balance': {'read_only': True},
        }


        def validate(self, attrs):
            payment_structure = attrs.get('payment_structure')

            if payment_structure == 'installments':
                # These fields are REQUIRED for installments
                if attrs.get('installment_number') is None:
                    raise serializers.ValidationError({
                        "installment_number": "This field is required for installment payments."
                    })
                if attrs.get('installment_amount') is None:
                    raise serializers.ValidationError({
                        "installment_amount": "This field is required for installment payments."
                    })
                if attrs.get('installment_amount') != attrs.get('payable_amount'):
                    raise serializers.ValidationError({
                        "installment_amount": "Must equal the payable_amount for this installment."
                    })

            elif payment_structure == 'One time':
                attrs.pop('installment_number', None)
                attrs.pop('installment_amount', None)

            return attrs

    def to_representation(self, instance):
        """
        Customize response: Hide installment fields if payment_structure is 'One time'
        """
        ret = super().to_representation(instance)

        payment_structure = instance.payment_structure or ret.get('payment_structure')

        if payment_structure != 'installments':
            ret.pop('installment_number', None)
            ret.pop('installment_amount', None)

     
        return ret









