from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


from authemail.models import EmailAbstractUser, EmailUserManager


class MyUser(EmailAbstractUser):
    objects = EmailUserManager()


class VerifiedUserManager(EmailUserManager):
    def get_queryset(self):
        return super(VerifiedUserManager, self).get_queryset().filter(
            is_verified=True)


class VerifiedUser(MyUser):
    objects = VerifiedUserManager()

    class Meta:
        proxy = True


class Pessoa(models.Model):
    user = models.OneToOneField(
        MyUser,
        on_delete=models.CASCADE,
        related_name='pessoa'
    )

    TIPO_PESSOA_CHOICES = [
        ('F', 'Pessoa Física'),
        ('J', 'Pessoa Jurídica'),
    ]

    tipo_pessoa = models.CharField(
        max_length=1,
        choices=TIPO_PESSOA_CHOICES
    )

    cpf_cnpj = models.CharField(
        max_length=14,
        unique=True
    )

    nome = models.CharField(max_length=150)

    confirmado = models.BooleanField(default=False)


class ContaCorrente(models.Model):
    pessoa = models.OneToOneField(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='conta_corrente'
    )

    agencia = models.CharField(max_length=10)
    numero = models.CharField(max_length=20, unique=True)

    saldo = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )

    criada_em = models.DateTimeField(auto_now_add=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.agencia}/{self.numero}'


class Movimentacao(models.Model):
    TIPO_OPERACAO_CHOICES = [
        ('D', 'Débito'),
        ('C', 'Crédito'),
    ]

    conta = models.ForeignKey(
        ContaCorrente,
        on_delete=models.CASCADE,
        related_name='movimentacoes'
    )

    tipo_operacao = models.CharField(
        max_length=1,
        choices=TIPO_OPERACAO_CHOICES
    )

    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    data_movimentacao = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        # flake8: noqa
        return f'{self.get_tipo_operacao_display()} - {self.valor}' # type: ignore 


