from django.urls import path, include
from rest_framework.routers import DefaultRouter
from investimentos.views import ClienteInvestidorViewSet, InvestimentoViewSet

router = DefaultRouter()
router.register(r'internal/clientes', ClienteInvestidorViewSet, 
                basename='cliente-investidor')
router.register(r'internal/investimentos', InvestimentoViewSet, 
                basename='investimento')

urlpatterns = [
    path('', include(router.urls)),
]