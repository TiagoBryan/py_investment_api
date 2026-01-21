from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from investimentos.models import ClienteInvestidor, Investimento
from investimentos.serializers import (ClienteInvestidorSerializer, 
                                       InvestimentoSerializer)
from rest_framework.exceptions import ValidationError
from django.db import transaction

from api_banco.models import Movimentacao 


class ClienteInvestidorViewSet(viewsets.ModelViewSet):
    queryset = ClienteInvestidor.objects.all()
    serializer_class = ClienteInvestidorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'pessoa'):
            serializer.save(pessoa=self.request.user.pessoa)  # type: ignore
        else:
            serializer.save()


class InvestimentoViewSet(viewsets.ModelViewSet):
    queryset = Investimento.objects.all()
    serializer_class = InvestimentoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], 
            url_path='cliente/(?P<cliente_id>[^/.]+)')
    def por_cliente(self, request, cliente_id=None):
        if cliente_id:
            cliente_id = cliente_id.strip()
        investimentos = self.queryset.filter(cliente__id=cliente_id)
        serializer = self.get_serializer(investimentos, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        user = self.request.user
        valor_investido = serializer.validated_data['valor_investido']
        
        try:
            conta = user.pessoa.conta_corrente  # type: ignore
        except Exception:
            raise ValidationError("Usuário não possui conta corrente ativa "
                                  "para realizar investimentos.")

        if valor_investido <= 0:
            raise ValidationError("O valor do investimento deve ser positivo.")

        if conta.saldo < valor_investido:
            raise ValidationError(f"Saldo insuficiente. Seu saldo atual é R$ \
                                  {conta.saldo}.")

        with transaction.atomic():
            conta.saldo -= valor_investido
            conta.save()

            Movimentacao.objects.create(
                conta=conta,
                tipo_operacao='D',
                valor=valor_investido
            )

            try:
                cliente_investidor = user\
                    .pessoa.perfil_investidor  # type: ignore
            except Exception:
                raise ValidationError("Perfil de investidor não encontrado.")

            serializer.save(cliente=cliente_investidor)

    def perform_destroy(self, instance):
        user = self.request.user
        valor_resgate = instance.valor_investido

        try:
            conta = user.pessoa.conta_corrente  # type: ignore
        except Exception:
            raise ValidationError("Conta corrente não encontrada para "
                                  "devolver o dinheiro.")

        with transaction.atomic():
            conta.saldo += valor_resgate
            conta.save()

            Movimentacao.objects.create(
                conta=conta,
                tipo_operacao='C',
                valor=valor_resgate
            )
    
            instance.delete()