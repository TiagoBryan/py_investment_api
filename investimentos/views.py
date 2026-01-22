from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from investimentos.models import ClienteInvestidor, Investimento
from investimentos.serializers import (ClienteInvestidorSerializer, 
                                       InvestimentoSerializer)
from rest_framework.exceptions import ValidationError
from django.db import transaction
from investimentos.services import MarketDataService
from api_banco.models import Movimentacao 
from decimal import Decimal
from rest_framework.views import APIView


class ClienteInvestidorViewSet(viewsets.ModelViewSet):
    serializer_class = ClienteInvestidorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ClienteInvestidor.objects.filter(pessoa__user=user)

    def perform_create(self, serializer):
        serializer.save(pessoa=self.request.user.pessoa)  # type: ignore

    def perform_destroy(self, instance):
        
        if instance.investimentos.filter(ativo=True).exists():
            raise ValidationError(
                "Não é possível cancelar o perfil pois existem investimentos "
                "ativos. "
                "Resgate todos os valores antes de continuar."
            )
        
        instance.delete()


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
        dados = serializer.validated_data
        
        tipo = dados.get('tipo_investimento')
        ticker = dados.get('ticker')
        quantidade = dados.get('quantidade')

        if tipo in ['ACOES', 'FUNDOS', 'CRIPTO']:
            if not ticker or not quantidade:
                raise ValidationError(
                    "Para Renda Variável, informe Ticker e Quantidade.")
            
            preco_atual = MarketDataService.validar_ticker(ticker)
            if preco_atual is None:
                raise ValidationError(
                    f"O ticker '{ticker}' não foi encontrado no mercado.")
            
            preco_compra = Decimal(str(preco_atual))
            valor_total_transacao = quantidade * preco_compra
            
        else:
            # renda fixa logica antiga colocar
            if not dados.get('valor_investido'):
                # nao mandou json (read only) lidar com isso
                pass
            valor_total_transacao = Decimal(0)

        try:
            conta = user.pessoa.conta_corrente  # type: ignore
        except Exception:
            raise ValidationError("Conta corrente não encontrada.")

        if conta.saldo < valor_total_transacao:
            raise ValidationError(f"Saldo insuficiente. \
                                  Custo da operação: \
                                  R$ {valor_total_transacao:.2f}")

        with transaction.atomic():
            conta.saldo -= valor_total_transacao
            conta.save()

            Movimentacao.objects.create(
                conta=conta,
                tipo_operacao='D',
                valor=valor_total_transacao
            )

            perfil = user.pessoa.perfil_investidor  # type: ignore

            serializer.save(
                cliente=perfil,
                preco_medio=preco_compra,
                valor_investido=valor_total_transacao
            )

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


class MarketProxyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        action = request.query_params.get('action')
        
        if action == 'quote':
            ticker = request.query_params.get('ticker')
            price = MarketDataService.get_latest_price(ticker)
            if price:
                return Response({'ticker': ticker.upper(), 'price': price})
            return Response({'error': 'Não encontrado'}, status=404)
            
        elif action == 'search':
            q = request.query_params.get('q')
            results = MarketDataService.search_assets(q)
            return Response(results)
            
        return Response({'error': 'Invalid action'}, status=400)