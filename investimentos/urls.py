from django.urls import path, include
from rest_framework.routers import DefaultRouter
from investimentos.views import (ClienteInvestidorViewSet, 
                                 InvestimentoViewSet,
                                 MarketProxyView,
                                 PortfolioAnalyticsView)

router = DefaultRouter()
router.register(r'internal/clientes', ClienteInvestidorViewSet, 
                basename='cliente-investidor')
router.register(r'internal/investimentos', InvestimentoViewSet, 
                basename='investimento')

urlpatterns = [
    path('', include(router.urls)),
    path('internal/market/', MarketProxyView.as_view(), name='market_proxy'),
    path('internal/analytics/cliente/<uuid:cliente_id>/', 
         PortfolioAnalyticsView.as_view(), name='portfolio_analytics'),
]