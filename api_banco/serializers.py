from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Pessoa, ContaCorrente, Movimentacao
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class MyUserSerializer(serializers.ModelSerializer):
    """
    Write your own User serializer.
    """
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'first_name', 'last_name')


class MyUserChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name')


class PessoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pessoa
        fields = (
            'id',
            'tipo_pessoa',
            'cpf_cnpj',
            'nome',
            'confirmado',
        )
        read_only_fields = ('confirmado',)

    def validate_cpf_cnpj(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "CPF/CNPJ deve conter apenas números."
            )

        if len(value) not in (11, 14):
            raise serializers.ValidationError(
                "CPF deve ter 11 dígitos e CNPJ 14 dígitos."
            )

        return value


class ContaCorrenteSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContaCorrente
        fields = (
            'id',
            'agencia',
            'numero',
            'saldo',
            'criada_em',
            'ativa'
        )
        read_only_fields = ('saldo', 'criada_em', 'ativa')

    def validate(self, attrs):
        pessoa = self.context['request'].user.pessoa

        if ContaCorrente.objects.filter(
            pessoa=pessoa,
            ativa=True
        ).exists():
            raise serializers.ValidationError(
                "Esta pessoa já possui uma conta corrente ativa."
            )

        if ContaCorrente.objects.filter(
            pessoa=pessoa,
            ativa=False
        ).exists():
            raise serializers.ValidationError(
                "Você desativou sua conta corrente. Entre em contato com o "
                "suporte."
            )

        return attrs

    def create(self, validated_data):
        validated_data['pessoa'] = self.context['request'].user.pessoa
        return super().create(validated_data)


class MovimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimentacao
        fields = (
            'id',
            'tipo_operacao',
            'valor',
            'data_movimentacao',
        )
        read_only_fields = ('data_movimentacao',)

    def validate_valor(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "O valor da movimentação deve ser maior que zero."
            )
        return value


class ContaCorrenteDeactivateSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        request = self.context['request']
        user = request.user

        if not user.check_password(value):
            raise serializers.ValidationError("Senha inválida.")

        return value


class OperacaoSerializer(serializers.Serializer):
    valor = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01
    )


class ClienteSignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)
    
    tipo_pessoa = serializers.ChoiceField(choices=Pessoa.TIPO_PESSOA_CHOICES)
    cpf_cnpj = serializers.CharField(max_length=14)

    def validate_email(self, value):
        User = get_user_model()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Um usuário com este e-mail "
                                              "já existe.")
        return value

    def validate_cpf_cnpj(self, value):
        clean_value = ''.join(filter(str.isdigit, value))
        
        if len(clean_value) not in (11, 14):
            raise serializers.ValidationError("CPF deve ter 11 dígitos e "
                                              "CNPJ 14.")
        
        if Pessoa.objects.filter(cpf_cnpj=clean_value).exists():
            raise serializers.ValidationError("Este CPF/CNPJ já está "
                                              "cadastrado.")
            
        return clean_value
    

class CustomLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    cpf_cnpj = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        cpf_cnpj_input = attrs.get('cpf_cnpj')

        user = authenticate(request=self.context.get('request'), 
                            email=email, password=password)

        if not user:
            raise serializers.ValidationError(
                _("Não foi possível fazer login com as credenciais "
                  "fornecidas.")
            )

        if not user.is_verified:  # type: ignore
            raise serializers.ValidationError(_("Conta de usuário não "
                                                "verificada."))
        if not user.is_active:
            raise serializers.ValidationError(_("Conta de usuário inativa."))

        try:
            cpf_clean = ''.join(filter(str.isdigit, cpf_cnpj_input))
            
            pessoa = user.pessoa  # type: ignore
            
            if pessoa.cpf_cnpj != cpf_clean:
                raise serializers.ValidationError(
                    _("O CPF/CNPJ informado não corresponde a este e-mail.")
                )
        except AttributeError:
            raise serializers.ValidationError(
                _("Este usuário não possui um perfil de Pessoa cadastrado.")
            )

        attrs['user'] = user
        return attrs
    

class UserDeactivateSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        request = self.context['request']
        user = request.user

        if not user.check_password(value):
            raise serializers.ValidationError("Senha incorreta.")

        return value