import pandas as pd
import numpy as np
from investimentos.services import MarketDataService


class PortfolioAnalytics:
    def __init__(self, investimentos_queryset):
        """
        Recebe um QuerySet de Investimentos (do Model).
        """
        self.investimentos = investimentos_queryset
        self.posicao_atual = {
            inv.ticker.upper(): float(inv.quantidade) 
            for inv in investimentos_queryset 
            if inv.ticker and inv.quantidade > 0
        }
        self.tickers = list(self.posicao_atual.keys())

    def calcular_performance(self, periodo="1y", benchmark_ticker="^BVSP"):
        """
        Gera todas as métricas necessárias para o Dashboard.
        """
        if not self.tickers:
            return None

        # Buscar Dados Históricos (Preços)
        df_precos = MarketDataService.get_historico_carteira(self.tickers, 
                                                             periodo)
        
        if df_precos.empty:
            return None

        # Calcular a Curva de Patrimônio (Valor R$ Diário)
        df_saldo = df_precos.copy()
        
        # Mapeamento para lidar com sulfixos (.SA) que o YFinance adiciona
        colunas_map = {}
        for col in df_precos.columns:
            ticker_sem_sa = col.replace('.SA', '')
            colunas_map[ticker_sem_sa] = col

        for ticker_db, qtd in self.posicao_atual.items():
            col_nome = colunas_map.get(ticker_db, ticker_db)
            
            if col_nome in df_saldo.columns:
                df_saldo[col_nome] = df_saldo[col_nome] * qtd
            else:
                pass

        df_saldo['Portfolio_Total'] = df_saldo.sum(axis=1)  # type: ignore

        # Calcular Retornos Percentuais (Variação Diária)
        series_retorno_diario = df_saldo['Portfolio_Total'].pct_change()\
            .dropna()
        
        # Calcular Retorno Acumulado (Curva % para gráfico)
        series_retorno_acumulado = (1 + series_retorno_diario).cumprod() - 1

        # Processar Benchmark (Comparativo)
        serie_bench = MarketDataService.get_historico_benchmark(
            benchmark_ticker, periodo)
        if not serie_bench.empty:
            serie_bench = serie_bench.reindex(series_retorno_diario.index)\
                .ffill()
            bench_retorno_diario = serie_bench.pct_change().dropna()
            bench_acumulado = (1 + bench_retorno_diario).cumprod() - 1
        else:
            bench_acumulado = pd.Series()

        # Calcular Métricas Estatísticas (KPIs)
        metricas = self._calcular_kpis(series_retorno_diario, 
                                       series_retorno_acumulado)

        # Preparar Dados para JSON (Frontend não lê Pandas/Numpy)
        return {
            "historico": {
                "datas": [d.strftime('%Y-%m-%d') 
                          for d in series_retorno_acumulado.index],
                "carteira_pct": (series_retorno_acumulado * 100).round(2)
                .tolist(),
                "benchmark_pct": (bench_acumulado * 100).round(2).tolist() if 
                not bench_acumulado.empty else []
            },
            "metricas": metricas
        }

    def _calcular_kpis(self, retornos_diarios, retorno_acumulado):
        try:
            if retorno_acumulado.empty:
                return {}

            retorno_total = retorno_acumulado.iloc[-1]

            dias = len(retornos_diarios)
            anos = dias / 252
            if anos > 0:
                retorno_anualizado = (1 + retorno_total) ** (1 / anos) - 1
            else:
                retorno_anualizado = 0.0

            volatilidade = retornos_diarios.std() * np.sqrt(252)

            return {
                "retorno_total_pct": float(round(retorno_total * 100, 2)),
                "retorno_anualizado_pct": float(round(retorno_anualizado * 100, 
                                                      2)),
                "volatilidade_pct": float(round(volatilidade * 100, 2)),
                "sharpe_ratio": 0.0
            }
        except Exception as e:
            print(f"Erro calculando KPIs: {e}")
            return {
                "retorno_total_pct": 0.0,
                "retorno_anualizado_pct": 0.0,
                "volatilidade_pct": 0.0
            }