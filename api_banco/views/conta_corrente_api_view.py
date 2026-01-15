from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from api_banco.models import ContaCorrente
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import status
from api_banco.serializers import (
                                 ContaCorrenteSerializer,
                                 ContaCorrenteDeactivateSerializer)


User = get_user_model()


class ContaCorrenteCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            conta = request.user.pessoa.conta_corrente

            serializer = ContaCorrenteSerializer(conta)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except AttributeError:
            return Response(
                {"detail": "Usuário não possui perfil de pessoa."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ContaCorrente.DoesNotExist:
            return Response(
                {"detail": "Conta corrente não encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        serializer = ContaCorrenteSerializer(data=request.data,
                                             context={'request': request})

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        pessoa = request.user.pessoa

        if hasattr(pessoa, 'conta_corrente'):
            return Response(
                {"detail": "Esta pessoa já possui uma conta corrente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        conta = ContaCorrente.objects.create(
            pessoa=pessoa,
            agencia=serializer.validated_data['agencia'],  # type: ignore
            numero=serializer.validated_data['numero'],  # type: ignore
        )

        return Response(
            ContaCorrenteSerializer(conta).data,
            status=status.HTTP_201_CREATED
        )


class ContaCorrenteDeactivateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, conta_id):
        serializer = ContaCorrenteDeactivateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        conta = get_object_or_404(
            ContaCorrente,
            id=conta_id,
            pessoa=request.user.pessoa,
            ativa=True
        )

        if conta.saldo != 0:
            return Response(
                {'error': 'A conta só pode ser desativada com saldo zerado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        conta.ativa = False
        conta.save()

        send_mail(
            subject='Conta corrente desativada',
            message=(
                f'Olá {request.user.pessoa.nome},\n\n'
                f'Sua conta {conta.agencia}/{conta.numero} '
                f'foi desativada com sucesso.\n\n'
                f'Se não foi você, entre em contato imediatamente.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        return Response(
            {'success': 'Conta desativada com sucesso.'},
            status=status.HTTP_200_OK
        )
