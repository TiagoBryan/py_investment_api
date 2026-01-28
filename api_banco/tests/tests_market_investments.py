from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from api_banco.models import Pessoa, ContaCorrente
from investimentos.models import Investimento

User = get_user_model()


class MarketInvestmentTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore
            email='trader@teste.com', password='123')
        self.pessoa = Pessoa.objects.create(
            user=self.user, nome='Trader', cpf_cnpj='11122233344', 
            tipo_pessoa='F'
        )
        self.conta = ContaCorrente.objects.create(
            pessoa=self.pessoa, agencia='0001', numero='50000',
            saldo=Decimal('1000.00'), ativa=True
        )
        from investimentos.models import ClienteInvestidor
        self.perfil = ClienteInvestidor.objects.create(
            pessoa=self.pessoa, perfil_investidor='ARROJADO', 
            patrimonio_total=0
        )
        
        self.client.force_authenticate(user=self.user)

    @patch('investimentos.services.MarketDataService.get_ticker_info')
    def test_comprar_acao_calculo_correto(self, mock_info):
        """
        deve calcular 10 cotas * preco50,00 = 500,00
        """
        mock_info.return_value = {'price': 50.00, 'currency': 'BRL'}

        url = reverse('investimento-list')
        data = {
            'tipo_investimento': 'ACOES',
            'ticker': 'PETR4',
            'quantidade': 10
        }

        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        mock_info.assert_called_with('PETR4')

        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, Decimal('500.00'))

        inv = Investimento.objects.last()
        self.assertEqual(inv.ticker, 'PETR4')  # type: ignore
        self.assertEqual(inv.quantidade,  # type: ignore
                         Decimal('10.00000000'))
        self.assertEqual(inv.preco_medio, Decimal('50.00'))  # type: ignore
        self.assertEqual(inv.valor_investido,  # type: ignore
                         Decimal('500.00')) 

    @patch('investimentos.services.MarketDataService.get_ticker_info')
    def test_comprar_ticker_inexistente(self, mock_info):
        mock_info.return_value = None

        url = reverse('investimento-list')
        data = {'tipo_investimento': 'ACOES', 'ticker': 'XYZ99', 
                'quantidade': 10}

        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('não foi encontrado', str(response.data))
        
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, Decimal('1000.00'))

    @patch('investimentos.services.MarketDataService.get_ticker_info')
    def test_market_proxy_quote(self, mock_info):
        mock_info.return_value = {'price': 35.50, 'currency': 'BRL'}
        
        url = reverse('market_proxy')
        response = self.client.get(url, {'action': 'quote', 'ticker': 'VALE3'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['price'], 35.50)

    def test_market_proxy_search(self):
        url = reverse('market_proxy')
        response = self.client.get(url, {'action': 'search', 'q': 'PETR'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(d['ticker'] == 'PETR4.SA' for d in response.data))