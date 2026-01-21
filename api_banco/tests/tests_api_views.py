from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from django.core import mail
from api_banco.models import Pessoa, ContaCorrente
from django.contrib.auth import get_user_model

User = get_user_model()


class BankAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects\
            .create_user(email='api@javer.com',  # type: ignore
                         password='123')
        self.pessoa = Pessoa.objects.create(
            user=self.user, nome='API User', cpf_cnpj='12345678900',
            tipo_pessoa='F'
        )
        self.conta = ContaCorrente.objects.create(
            pessoa=self.pessoa, agencia='0001', numero='12345',
            saldo=Decimal('100.00'), ativa=True
        )
        self.client.force_authenticate(user=self.user)  # type: ignore

    def test_criar_conta_duplicada(self):
        url = reverse('api_conta_create')
        data = {'agencia': '0002', 'numero': '99999'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deposito_api(self):
        url = reverse('api_deposito')
        data = {'valor': '50.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, Decimal('150.00'))

    def test_saque_api_insuficiente(self):
        url = reverse('api_saque')
        data = {'valor': '200.00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_desativar_conta_sucesso(self):
        self.conta.saldo = Decimal('0.00')
        self.conta.save()
        url = reverse('api_conta_desativar',
                      args=[self.conta.id])  # type: ignore
        data = {'password': '123'}

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.conta.refresh_from_db()
        self.assertFalse(self.conta.ativa)
        self.assertTrue(len(mail.outbox) > 0)

    def test_login_custom_sucesso(self):
        """Testa se o login aceita CPF correto"""
        # Cria usuario e pessoa
        user = User.objects.create_user(
            email='login@teste.com',  # type: ignore
            password='123')
        user.is_verified = True  # type: ignore
        user.save()
        Pessoa.objects.create(user=user, cpf_cnpj='11122233344',
                              tipo_pessoa='F', nome='Login')

        url = reverse('api_login_custom')
        data = {
            'email': 'login@teste.com',
            'password': '123',
            'cpf_cnpj': '111.222.333-44'  # Enviando ponto (serializer limpa)
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)  # type: ignore

    def test_login_custom_cpf_errado(self):
        """Testa se o login rejeita CPF que não bate com o email"""
        user = User.objects.create_user(
            email='login2@teste.com',  # type: ignore
            password='123')
        user.is_verified = True  # type: ignore
        user.save()
        Pessoa.objects.create(user=user, cpf_cnpj='11122233344',
                              tipo_pessoa='F', nome='Login')

        url = reverse('api_login_custom')
        data = {
            'email': 'login2@teste.com',
            'password': '123',
            'cpf_cnpj': '99999999999'  # CPF diferente
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verifica se a mensagem customizada apareceu
        self.assertTrue("não corresponde" in str(response
                                                 .data))  # type: ignore

    def test_signup_api_completo(self):
        """Testa se o endpoint de cadastro cria User + Pessoa + Envia Email"""
        url = reverse('api_signup_cliente')  # Verifique o name no urls.py
        data = {
            'first_name': 'Novo',
            'last_name': 'User',
            'email': 'novo@api.com',
            'password': '123',
            'tipo_pessoa': 'F',
            'cpf_cnpj': '55566677788'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verifica se criou no banco
        self.assertTrue(User.objects.filter(email='novo@api.com').exists())
        self.assertTrue(Pessoa.objects.filter(cpf_cnpj='55566677788').exists())

        # Verifica se o usuario criado nao está verificado (segurança)
        user = User.objects.get(email='novo@api.com')
        self.assertFalse(user.is_verified)  # type: ignore

    def test_acesso_negado_sem_token(self):
        """Tenta sacar sem estar logado"""
        self.client.logout()  # Garante que não tem token

        url = reverse('api_saque')
        data = {'valor': '10.00'}

        response = self.client.post(url, data)

        # Deve retornar 401 Unauthorized ou 403 Forbidden
        self.assertIn(response.status_code, [401, 403])
