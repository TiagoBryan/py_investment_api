from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from django.contrib.auth import get_user_model
from api_banco.models import Pessoa, ContaCorrente, Movimentacao
from investimentos.models import ClienteInvestidor, Investimento

User = get_user_model()


class InvestimentosAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore
                                             email='investidor@teste.com', 
                                             password='123')
        self.pessoa = Pessoa.objects.create(
            user=self.user, nome='Investidor', cpf_cnpj='11122233344', 
            tipo_pessoa='F'
        )
        
        self.conta = ContaCorrente.objects.create(
            pessoa=self.pessoa, agencia='0001', numero='10000',
            saldo=Decimal('1000.00'), ativa=True
        )

        self.perfil = ClienteInvestidor.objects.create(
            pessoa=self.pessoa,
            perfil_investidor='MODERADO',
            patrimonio_total=Decimal('0.00')
        )

        self.client.force_authenticate(user=self.user)  # type: ignore

    def test_investir_sucesso_movimentacao_saldo(self):
        url = reverse('investimento-list') 
        data = {
            'tipo_investimento': 'ACOES',
            'valor_investido': '200.00'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verifica Saldo (1000 - 200 = 800)
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, Decimal('800.00'))

        # Verifica Extrato
        mov = Movimentacao.objects.last()
        self.assertEqual(mov.tipo_operacao, 'D')  # type: ignore
        self.assertEqual(mov.valor, Decimal('200.00'))  # type: ignore

    def test_investir_sem_saldo(self):
        """Deve bloquear investimento maior que o saldo"""
        url = reverse('investimento-list')
        data = {
            'tipo_investimento': 'CRIPTO',
            'valor_investido': '1500.00'  # Maior que 1000
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Saldo insuficiente', str(response.data))  # type: ignore

        # Saldo intacto
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, Decimal('1000.00'))

    def test_resgatar_investimento_devolve_dinheiro(self):
        """Ao deletar investimento, o dinheiro deve voltar para a conta"""
        self.conta.saldo = Decimal('500.00')
        self.conta.save()
        
        inv = Investimento.objects.create(
            cliente=self.perfil,
            tipo_investimento='FUNDOS',
            valor_investido=Decimal('500.00'),
            ativo=True
        )

        url = reverse('investimento-detail', args=[inv.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Saldo deve voltar para 1000 (500 inicial + 500 devolvido)
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, Decimal('1000.00'))
        
        # Verifica Extrato (Crédito)
        mov = Movimentacao.objects.last()
        self.assertEqual(mov.tipo_operacao, 'C')  # type: ignore

    def test_tentar_excluir_perfil_com_investimento(self):
        """
        Bloqueia exclusão do PERFIL se houver investimento ativo.
        (Testa o perform_destroy do ClienteInvestidorViewSet)
        """
        Investimento.objects.create(
            cliente=self.perfil,
            tipo_investimento='RENDA_FIXA',
            valor_investido=Decimal('100.00'),
            ativo=True
        )

        url = reverse('cliente-investidor-detail', args=[self.perfil.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('investimentos ativos', 
                      str(response.data))  # type: ignore
        
        # Perfil ainda existe
        self.assertTrue(ClienteInvestidor.objects.filter(id=self.perfil.id)
                        .exists())

    def test_atualizar_perfil_investidor(self):
        """Testa mudar de MODERADO para ARROJADO"""
        url = reverse('cliente-investidor-detail', args=[self.perfil.id])
        data = {'perfil_investidor': 'ARROJADO'}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.perfil_investidor, 'ARROJADO')