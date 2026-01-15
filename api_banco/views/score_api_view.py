from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from api_banco.models import ContaCorrente

from decimal import Decimal
from rest_framework.permissions import IsAuthenticated

from rest_framework import status


User = get_user_model()


class ScoreCreditoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pessoa = request.user.pessoa

        try:
            conta = pessoa.conta_corrente
        except ContaCorrente.DoesNotExist:
            return Response(
                {"detail": "Pessoa não possui conta corrente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        score = conta.saldo * Decimal("0.1")

        return Response(
            {
                "saldo": conta.saldo,
                "score_credito": score
            },
            status=status.HTTP_200_OK
        )
