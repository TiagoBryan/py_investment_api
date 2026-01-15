from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from authemail.admin import EmailUserAdmin

from api_banco.models import (
    Pessoa,
    ContaCorrente,
    Movimentacao,
    VerifiedUser,
)

MyUser = get_user_model()


class PessoaInline(admin.StackedInline):
    model = Pessoa
    can_delete = False
    extra = 0
    verbose_name = 'Pessoa'
    verbose_name_plural = 'Dados da Pessoa'


class MovimentacaoInline(admin.TabularInline):
    model = Movimentacao
    extra = 0
    can_delete = False
    readonly_fields = (
        'tipo_operacao',
        'valor',
        'data_movimentacao',
    )
    verbose_name = 'Movimentação'
    verbose_name_plural = 'Movimentações'


class MyUserAdmin(EmailUserAdmin):
    list_display = (
        'id',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_verified',
        'is_staff',
        'date_joined',
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
    )

    ordering = ('-date_joined',)

    inlines = [PessoaInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_verified',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )


class VerifiedUserAdmin(MyUserAdmin):
    readonly_fields = ('email',)

    def has_add_permission(self, request):
        return False


@admin.register(ContaCorrente)
class ContaCorrenteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'agencia',
        'numero',
        'pessoa',
        'saldo',
        'criada_em',
    )

    search_fields = (
        'numero',
        'agencia',
        'pessoa__cpf_cnpj',
        'pessoa__nome',
    )

    list_filter = (
        'agencia',
        'criada_em',
    )

    ordering = ('-criada_em',)

    inlines = [MovimentacaoInline]


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'conta',
        'tipo_operacao',
        'valor',
        'data_movimentacao',
    )

    list_filter = (
        'tipo_operacao',
        'data_movimentacao',
    )

    search_fields = (
        'conta__numero',
    )

    ordering = ('-data_movimentacao',)


admin.site.unregister(MyUser)
admin.site.register(MyUser, MyUserAdmin)
admin.site.register(VerifiedUser, VerifiedUserAdmin)
