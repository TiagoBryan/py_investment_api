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
        ("FUNDOS", "Fundos"),
        ("CRIPTO", "Criptomoedas"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    cliente = models.ForeignKey(
        ClienteInvestidor, 
        on_delete=models.CASCADE, 
        related_name='investimentos'
    )
    
    tipo_investimento = models.CharField(max_length=20, 
                                         choices=TIPO_INVESTIMENTO_CHOICES)
    valor_investido = models.DecimalField(max_digits=15, decimal_places=2)
    data_aplicacao = models.DateTimeField(auto_now_add=True)
    
    rentabilidade = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    ativo = models.BooleanField(default=True)

    def __str__(self):
        tipo_investimento = self\
            .get_tipo_investimento_display()  # type: ignore
        return f"{tipo_investimento} - {self.valor_investido}"