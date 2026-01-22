from rest_framework import serializers
from investimentos.models import ClienteInvestidor, Investimento


class InvestimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investimento
        fields = '__all__'
        read_only_fields = ['id', 'cliente', 'data_aplicacao', 
                            'valor_investido', 'ativo', 'preco_medio']


class ClienteInvestidorSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='pessoa.nome', read_only=True)
    cpf = serializers.CharField(source='pessoa.cpf_cnpj', read_only=True)
    email = serializers.EmailField(source='pessoa.user.email', read_only=True)
    
    investimentos = InvestimentoSerializer(many=True, read_only=True)

    class Meta:
        model = ClienteInvestidor
        fields = [
            'id', 'nome', 'cpf', 'email', 
            'perfil_investidor', 'patrimonio_total', 
            'data_cadastro', 'investimentos'
        ]
        read_only_fields = ['id', 'data_cadastro']