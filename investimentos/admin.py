from django.contrib import admin
from .models import ClienteInvestidor, Investimento


class InvestimentoInline(admin.TabularInline):
    model = Investimento
    extra = 0
    readonly_fields = ('data_aplicacao',)
    can_delete = True
    fields = ('tipo_investimento', 'valor_investido', 'rentabilidade', 
              'ativo', 'data_aplicacao')


@admin.register(ClienteInvestidor)
class ClienteInvestidorAdmin(admin.ModelAdmin):
    list_display = (
        'get_nome', 
        'perfil_investidor', 
        'get_patrimonio_formatado', 
        'data_cadastro'
    )
    
    search_fields = (
        'pessoa__nome', 
        'pessoa__cpf_cnpj', 
        'pessoa__user__email'
    )
    
    list_filter = ('perfil_investidor', 'data_cadastro')
    
    inlines = [InvestimentoInline]

    list_select_related = ('pessoa',)

    @admin.display(description='Nome do Cliente', ordering='pessoa__nome')
    def get_nome(self, obj):
        return obj.pessoa.nome

    @admin.display(description='Patrimônio Inicial')
    def get_patrimonio_formatado(self, obj):
        return f"R$ {obj.patrimonio_total:,.2f}"


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = (
        'get_cliente_nome', 
        'tipo_investimento', 
        'get_valor_formatado', 
        'ativo', 
        'data_aplicacao'
    )
    
    search_fields = ('cliente__pessoa__nome', 'cliente__pessoa__cpf_cnpj')
    
    list_filter = ('tipo_investimento', 'ativo', 'data_aplicacao')
    
    list_select_related = ('cliente', 'cliente__pessoa')

    @admin.display(description='Investidor', ordering='cliente__pessoa__nome')
    def get_cliente_nome(self, obj):
        return obj.cliente.pessoa.nome

    @admin.display(description='Valor Investido')
    def get_valor_formatado(self, obj):
        return f"R$ {obj.valor_investido:,.2f}"