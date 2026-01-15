from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from api_banco import views
from .views import (
    ContaCorrenteCreateAPIView,
    MovimentacaoCreateAPIView,
    ContaCorrenteDeactivateAPIView,
    DepositoAPIView,
    SaqueAPIView,
    ScoreCreditoAPIView,
    ClienteSignupAPIView,
    CustomLoginAPIView,
    UserDeactivateAPIView
)


urlpatterns = [
    path('users/me/', views.MyUserMe.as_view(), name='api_users_me'),
    path('users/me/change/', views.MyUserMeChange.as_view(),
         name='api_users_me_change'),
    path('contas/', ContaCorrenteCreateAPIView.as_view(),
         name='api_conta_create'),
    path(
        'contas/<int:conta_id>/movimentacoes/',
        MovimentacaoCreateAPIView.as_view(),
        name='api_movimentacao_create'
    ),
    path(
        'contas/<int:conta_id>/desativar/',
        ContaCorrenteDeactivateAPIView.as_view(),
        name='api_conta_desativar'
    ),
    path('conta/deposito/', DepositoAPIView.as_view(), name='api_deposito'),
    path('conta/saque/', SaqueAPIView.as_view(), name='api_saque'),
    path('conta/score/', ScoreCreditoAPIView.as_view(), name='api_score'),
    path('signup/cliente/', ClienteSignupAPIView.as_view(),
         name='api_signup_cliente'),
    path('login/custom/', CustomLoginAPIView.as_view(),
         name='api_login_custom'),
    path('users/me/desativar/', UserDeactivateAPIView.as_view(),
         name='api_user_deactivate'),

]


urlpatterns = format_suffix_patterns(urlpatterns)
