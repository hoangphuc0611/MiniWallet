from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.views import ObtainAuthToken
from api.models import *
from rest_framework import status


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        customer_xid = request.POST.get('customer_xid')
        customer = Customer.objects.filter(id=customer_xid).first()
        if not customer:
            customer = Customer.objects.create(id=customer_xid)
        token, created = Token.objects.get_or_create(user=customer)
        return Response({"data": {"token": token.key}, "status": "success"})


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        token = request.headers.get('Authorization').split(
        )[1] if request.headers.get('Authorization').split()[1] else ''
        token, create_at = Token.objects.get_or_create(key=token)
        customer = Customer.objects.filter(id=token.user_id).first()
        if not customer:
            return Response({'message': 'Customer not found'},
                            status=status.HTTP_404_NOT_FOUND)
        wallet = Wallet.objects.filter(owned_by=customer).first()
        if not wallet:
            return Response({'message': 'Wallet not found'},
                            status=status.HTTP_404_NOT_FOUND)
        content = {
            "status": "success",
            "data": {
                "wallet": {
                    "id": wallet.id,
                    "owned_by": token.user_id,
                    "status": wallet.status,
                    "enabled_at": wallet.enabled_at,
                    "balance": wallet.balance
                }
            }
        }
        return Response(content, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        token = request.headers.get('Authorization').split(
        )[1] if request.headers.get('Authorization').split()[1] else ''
        token, create_at = Token.objects.get_or_create(key=token)
        customer = Customer.objects.filter(id=token.user_id).first()
        if not customer:
            return Response({'message': 'Customer not found'},
                            status=status.HTTP_404_NOT_FOUND)

        wallet = Wallet.objects.filter(owned_by=customer).first()
        if not wallet:
            wallet = Wallet.objects.create(owned_by=customer,
                                           status='enabled',
                                           balance=0)[0]
        else:
            wallet.status = 'enabled'
            wallet.save()

        content = {
            "status": "success",
            "data": {
                "wallet": {
                    "id": wallet.id,
                    "owned_by": token.user_id,
                    "status": wallet.status,
                    "enabled_at": wallet.enabled_at,
                    "balance": wallet.balance
                }
            }
        }
        return Response(content)

    def patch(self, request, format=None):
        is_disabled = request.POST.get('is_disabled')
        if not is_disabled:
            return Response(
                {
                    'message':
                    'Required parameter is missing or invalid in body request'
                },
                status=status.HTTP_400_BAD_REQUEST)
        elif is_disabled not in ['true', 'false']:
            return Response({'message': 'is_disabled should be true or false'},
                            status=status.HTTP_400_BAD_REQUEST)

        token = request.headers.get('Authorization').split(
        )[1] if request.headers.get('Authorization').split()[1] else ''
        token, create_at = Token.objects.filter(key=token).first()
        customer = Customer.objects.filter(id=token.user_id).first()
        if not customer:
            return Response({'message': 'Customer not found'},
                            status=status.HTTP_404_NOT_FOUND)

        wallet = Wallet.objects.filter(owned_by=customer).first()

        if not wallet:
            return Response({'message': 'Wallet not found'},
                            status=status.HTTP_404_NOT_FOUND)

        if is_disabled == 'true':
            wallet.status = 'disabled'
        else:
            wallet.status = 'enabled'
        wallet.save()
        content = {
            "status": "success",
            "data": {
                "wallet": {
                    "id": wallet.id,
                    "owned_by": token.user_id,
                    "status": wallet.status,
                    "enabled_at": wallet.enabled_at,
                    "balance": wallet.balance
                }
            }
        }
        return Response(content)


class DepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        token = request.headers.get('Authorization').split(
        )[1] if request.headers.get('Authorization').split()[1] else ''
        token, create_at = Token.objects.get_or_create(key=token)
        amount = request.POST.get('amount')
        reference_id = request.POST.get('reference_id')
        if not amount or not reference_id:
            return Response(
                {
                    'message':
                    'Required parameter is missing or invalid in body request'
                },
                status=status.HTTP_400_BAD_REQUEST)

        customer = Customer.objects.filter(id=token.user_id).first()
        if not customer:
            return Response({'message': 'Customer not found'},
                            status=status.HTTP_404_NOT_FOUND)

        deposit_exits = Deposit.objects.filter(reference_id=reference_id)
        if deposit_exits:
            return Response({'message': 'reference_id existed'},
                            status=status.HTTP_400_BAD_REQUEST)
        deposit = Deposit.objects.create(deposited_by=customer,
                                         status='success',
                                         amount=amount,
                                         reference_id=reference_id)[0]
        wallet = Wallet.objects.filter(owned_by=customer).first()
        if not wallet:
            return Response({'message': 'Wallet not found'},
                            status=status.HTTP_404_NOT_FOUND)
        if wallet.status != 'enabled':
            return Response({'message': "Wallet hasn't enable yet"},
                            status=status.HTTP_400_BAD_REQUEST)

        wallet.balance += int(amount)
        wallet.save()
        content = {
            "status": "success",
            "data": {
                "deposit": {
                    "id": deposit.id,
                    "deposited_by": customer.id,
                    "status": "success",
                    "deposited_at": deposit.deposited_at,
                    "amount": deposit.amount,
                    "reference_id": deposit.reference_id
                }
            }
        }
        return Response(content)


class WithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        amount = request.POST.get('amount')
        reference_id = request.POST.get('reference_id')
        if not amount or not reference_id:
            return Response(
                {
                    'message':
                    'Required parameter is missing or invalid in body request'
                },
                status=status.HTTP_400_BAD_REQUEST)

        token = request.headers.get('Authorization').split(
        )[1] if request.headers.get('Authorization').split()[1] else ''
        token, create_at = Token.objects.get_or_create(key=token)

        customer = Customer.objects.get(id=token.user_id)
        withdrawn_exist = Withdrawal.objects.filter(
            reference_id=reference_id).first()
        if withdrawn_exist:
            return Response({'message': 'reference_id existed'},
                            status=status.HTTP_400_BAD_REQUEST)

        withdrawn = Withdrawal.objects.create(withdrawn_by=customer,
                                              status='success',
                                              amount=amount,
                                              reference_id=reference_id)

        wallet = Wallet.objects.filter(owned_by=customer).first()
        if not wallet:
            return Response({'message': 'Wallet not found'},
                            status=status.HTTP_404_NOT_FOUND)
        if wallet.status != 'enabled':
            return Response({'message': "Wallet hasn't enable yet"},
                            status=status.HTTP_400_BAD_REQUEST)
        wallet.balance -= int(amount)
        wallet.save()
        content = {
            "status": "success",
            "data": {
                "withdrawal": {
                    "id": withdrawn.id,
                    "withdrawn_by": customer.id,
                    "status": "success",
                    "withdrawn_at": withdrawn.withdrawn_at,
                    "amount": withdrawn.amount,
                    "reference_id": withdrawn.reference_id
                }
            }
        }
        return Response(content, status=status)
