from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from api_banco.models import ContaCorrente, Movimentacao
from decimal import Decimal
from rest_framework.permissions import IsAuthenticated

from rest_framework import status
from api_banco.serializers import (
                                 MovimentacaoSerializer,
                                 )


User = get_user_model()


class MovimentacaoCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conta_id):
        serializer = MovimentacaoSerializer(data=request.data)

        if serializer.is_valid():

            conta = ContaCorrente.objects.get(
                id=conta_id,
                pessoa=request.user.pessoa
            )

            movimentacao = Movimentacao.objects.create(
                conta=conta,
                tipo_operacao=serializer
                .validated_data['tipo_operacao'],  # type: ignore
                valor=serializer.validated_data['valor']  # type: ignore
            )

            if movimentacao.tipo_operacao == 'D':
                conta.saldo -= movimentacao.valor
            else:
                conta.saldo += movimentacao.valor

            conta.save()

            return Response(
                MovimentacaoSerializer(movimentacao).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepositoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pessoa = request.user.pessoa

        try:
            conta = pessoa.conta_corrente
        except ContaCorrente.DoesNotExist:
            return Response(
                {"detail": "Pessoa não possui conta corrente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        valor = Decimal(request.data.get("valor", 0))

        if valor <= 0:
            return Response(
                {"detail": "Valor inválido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        conta.saldo += valor
        conta.save()

        Movimentacao.objects.create(
            conta=conta,
            tipo_operacao='C',
            valor=valor
        )

        return Response(
            {"detail": "Depósito realizado com sucesso."},
            status=status.HTTP_200_OK
        )


class SaqueAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pessoa = request.user.pessoa

        try:
            conta = pessoa.conta_corrente
        except ContaCorrente.DoesNotExist:
            return Response(
                {"detail": "Pessoa não possui conta corrente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        valor = Decimal(request.data.get("valor", 0))

        if valor <= 0:
            return Response(
                {"detail": "Valor inválido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if conta.saldo < valor:
            return Response(
                {"detail": "Saldo insuficiente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        conta.saldo -= valor
        conta.save()

        Movimentacao.objects.create(
            conta=conta,
            tipo_operacao='D',
            valor=valor
        )

        return Response(
            {"detail": "Saque realizado com sucesso."},
            status=status.HTTP_200_OK
        )
