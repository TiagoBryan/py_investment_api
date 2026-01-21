from django.test import TestCase
from django.db.utils import IntegrityError
from decimal import Decimal
from api_banco.models import Pessoa, ContaCorrente, Movimentacao
from django.contrib.auth import get_user_model

User = get_user_model()


class ModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(  # type: ignore
            email='cliente@javer.com',
            password='senha_segura_123',
            first_name='Cliente',
            last_name='Teste'
        )
        self.pessoa = Pessoa.objects.create(
            user=self.user,
            tipo_pessoa='F',
            cpf_cnpj='12345678900',
            nome='Cliente Teste'
        )

    def test_pessoa_criacao(self):
        self.assertEqual(self.pessoa.nome, 'Cliente Teste')
        self.assertEqual(self.pessoa.user.email, 'cliente@javer.com')

    def test_cpf_cnpj_unico(self):
        user2 = User.objects\
            .create_user(email='oloko@teste.com',  # type: ignore
                         password='123')
        with self.assertRaises(IntegrityError):
            Pessoa.objects.create(
                user=user2,
                tipo_pessoa='F',
                cpf_cnpj='12345678900',  # Repetido
                nome='Impostor'
            )

    def test_conta_criacao_padrao(self):
        conta = ContaCorrente.objects.create(
            pessoa=self.pessoa,
            agencia='0001',
            numero='99999-X'
        )
        self.assertTrue(conta.ativa)
        self.assertEqual(conta.saldo, Decimal('0.00'))

    def test_conta_numero_unico(self):
        ContaCorrente.objects.create(pessoa=self.pessoa, agencia='0001',
                                     numero='12345')

        user2 = User.objects\
            .create_user(email='outro@javer.com',  # type: ignore
                         password='123')
        pessoa2 = Pessoa.objects.create(user=user2, cpf_cnpj='99988877700',
                                        nome='Outro', tipo_pessoa='F')

        with self.assertRaises(IntegrityError):
            ContaCorrente.objects.create(
                pessoa=pessoa2,
                agencia='0002',
                numero='12345'
            )

    def test_movimentacao_registro(self):
        conta = ContaCorrente.objects.create(pessoa=self.pessoa,
                                             agencia='0001', numero='55555')
        mov = Movimentacao.objects.create(
            conta=conta,
            tipo_operacao='C',
            valor=Decimal('150.50')
        )
        self.assertEqual(mov.valor, Decimal('150.50'))
