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
from investimentos.analytics import PortfolioAnalytics


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
        
        valor_total_transacao_brl = Decimal(0)
        preco_compra_brl = Decimal(0)
        quantidade_final = Decimal(0)
        ticker_final = None

        if tipo in ['ACOES', 'FUNDOS', 'CRIPTO']:
            ticker = dados.get('ticker')
            quantidade = dados.get('quantidade')
            ticker_final = ticker

            info_ativo = MarketDataService.get_ticker_info(ticker)
            
            if not info_ativo:
                raise ValidationError(
                    f"O ticker '{ticker}' não foi encontrado.")
            
            preco_original = Decimal(str(info_ativo['price']))
            moeda = info_ativo['currency']
            
            taxa_dolar = Decimal(1.0)
            
            if moeda == 'USD':
                rate = MarketDataService.get_dolar_rate()
                if not rate:
                    raise ValidationError("Erro ao obter cotação do Dólar.")
                taxa_dolar = Decimal(str(rate))
                
                preco_compra_brl = preco_original * taxa_dolar
            else:
                preco_compra_brl = preco_original

            quantidade_final = quantidade
            valor_total_transacao_brl = quantidade * preco_compra_brl
            
        else:
            valor_raw = self\
                .request.data.get('valor_investido')  # type: ignore
            valor_total_transacao_brl = Decimal(str(valor_raw))
            preco_compra_brl = Decimal("1.00")
            quantidade_final = valor_total_transacao_brl

        try:
            conta = user.pessoa.conta_corrente  # type: ignore
        except Exception:
            raise ValidationError("Conta corrente não encontrada.")

        if conta.saldo < valor_total_transacao_brl:
            raise ValidationError(
                f"Saldo insuficiente. Custo: R$ \
                      {valor_total_transacao_brl:.2f}")

        with transaction.atomic():
            conta.saldo -= valor_total_transacao_brl
            conta.save()

            Movimentacao.objects.create(
                conta=conta,
                tipo_operacao='D',
                valor=valor_total_transacao_brl
            )

            try:
                perfil = user.pessoa.perfil_investidor  # type: ignore
            except Exception:
                raise ValidationError("Perfil de investidor não encontrado.")

            serializer.save(
                cliente=perfil,
                ticker=ticker_final,
                quantidade=quantidade_final,
                preco_medio=preco_compra_brl,
                valor_investido=valor_total_transacao_brl
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

            info = MarketDataService.get_ticker_info(ticker)
            
            if info:
                response_data = {
                    'ticker': ticker.upper(),
                    'price': info['price'],
                    'currency': info['currency']
                }
                
                if info['currency'] == 'USD':
                    response_data['exchange_rate'] = MarketDataService\
                        .get_dolar_rate()
                
                return Response(response_data)
                
        return Response({'error': 'Não encontrado'}, status=404)
        

class PortfolioAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, cliente_id=None):
        """
        calcula a performance historica da carteira do cliente.
        URL: /api/internal/analytics/cliente/{id}/?periodo=1y
        """
        if not cliente_id and hasattr(request.user, 'pessoa'):
            try:
                cliente_id = request.user.pessoa.perfil_investidor.id
            except Exception:
                return Response({'error': 'Perfil não encontrado'}, status=404)

        investimentos = Investimento.objects.filter(
            cliente__id=cliente_id, 
            ativo=True
        )

        if not investimentos.exists():
            return Response({'error': 'Sem investimentos ativos'}, status=404)

        periodo = request.query_params.get('periodo', '1y')
        valid_periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'ytd']
        if periodo not in valid_periods:
            periodo = '1y'

        try:
            analytics = PortfolioAnalytics(investimentos)
            dados = analytics.calcular_performance(periodo=periodo)
            
            if not dados:
                return Response({'error': 'Dados insuficientes para cálculo'}, 
                                status=400)
                
            return Response(dados)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)