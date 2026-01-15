from django.test import TestCase
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api_banco.serializers import (
    PessoaSerializer,
    MovimentacaoSerializer,
    ContaCorrenteDeactivateSerializer,
)

User = get_user_model()


class SerializersTest(TestCase):
    def setUp(self):
        self.user = User.objects\
            .create_user(email='teste@javer.com',  # type: ignore
                         password='123')

    def test_pessoa_serializer_cpf_valido(self):
        data = {
            'tipo_pessoa': 'F',
            'cpf_cnpj': '12345678900',
            'nome': 'Teste',
            'confirmado': False
        }
        serializer = PessoaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_pessoa_serializer_cpf_invalido(self):
        data_letras = {'tipo_pessoa': 'F', 'cpf_cnpj': '1234567890A',
                       'nome': 'Teste'}
        ser_letras = PessoaSerializer(data=data_letras)
        self.assertFalse(ser_letras.is_valid())
        self.assertIn('cpf_cnpj', ser_letras.errors)

    def test_movimentacao_serializer_valor(self):
        ser_zero = MovimentacaoSerializer(data={'tipo_operacao': 'D',
                                                'valor': '0.00'})
        self.assertFalse(ser_zero.is_valid())

        ser_ok = MovimentacaoSerializer(data={'tipo_operacao': 'C',
                                              'valor': '50.00'})
        self.assertTrue(ser_ok.is_valid())

    def test_deactivate_serializer_password(self):
        factory = RequestFactory()
        request = factory.post('/')
        request.user = self.user

        ser_ok = ContaCorrenteDeactivateSerializer(
            data={'password': '123'},
            context={'request': request}
        )
        self.assertTrue(ser_ok.is_valid())

        ser_fail = ContaCorrenteDeactivateSerializer(
            data={'password': 'errada'},
            context={'request': request}
        )
        self.assertFalse(ser_fail.is_valid())
