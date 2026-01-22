import uuid
from django.db import models
from api_banco.models import Pessoa
from decimal import Decimal


class ClienteInvestidor(models.Model):
    PERFIL_CHOICES = [
        ("CONSERVADOR", "Conservador"),
        ("MODERADO", "Moderado"),
        ("ARROJADO", "Arrojado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    pessoa = models.OneToOneField(
        Pessoa, 
        on_delete=models.CASCADE, 
        related_name='perfil_investidor'
    )
    
    perfil_investidor = models.CharField(
        max_length=20, 
        choices=PERFIL_CHOICES,
        default="CONSERVADOR"
    )
    
    patrimonio_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pessoa.nome} - {self.perfil_investidor}"


class Investimento(models.Model):
    TIPO_INVESTIMENTO_CHOICES = [
        ("RENDA_FIXA", "Renda Fixa"),
        ("ACOES", "Ações"),
        ("FUNDOS", "Fundos Imobiliários (FIIs)"),
        ("CRIPTO", "Criptomoedas"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    cliente = models.ForeignKey(
        'ClienteInvestidor',
        on_delete=models.CASCADE, 
        related_name='investimentos'
    )
    
    tipo_investimento = models.CharField(max_length=20, 
                                         choices=TIPO_INVESTIMENTO_CHOICES)
    
    ticker = models.CharField(max_length=20, blank=True, null=True, 
                              help_text="Ex: PETR4, BTC-USD")
    quantidade = models.DecimalField(max_digits=15, decimal_places=8, 
                                     default=Decimal('0.00'))
    preco_medio = models.DecimalField(max_digits=15, decimal_places=2, 
                                      default=Decimal('0.00'))

    valor_investido = models.DecimalField(max_digits=15, decimal_places=2)
    
    data_aplicacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.quantidade and self.preco_medio:
            self.valor_investido = self.quantidade * self.preco_medio
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticker} - Qtd: {self.quantidade}"