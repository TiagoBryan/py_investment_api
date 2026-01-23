import yfinance as yf
import pandas as pd


class MarketDataService:
    POPULAR_ASSETS = [
        {"ticker": "PETR4.SA", "nome": "Petrobras PN", "tipo": "ACOES"},
        {"ticker": "VALE3.SA", "nome": "Vale ON", "tipo": "ACOES"},
        {"ticker": "ITUB4.SA", "nome": "Itaú Unibanco PN", "tipo": "ACOES"},
        {"ticker": "BBDC4.SA", "nome": "Bradesco PN", "tipo": "ACOES"},
        {"ticker": "WEGE3.SA", "nome": "WEG ON", "tipo": "ACOES"},
        {"ticker": "MXRF11.SA", "nome": "Maxi Renda FII", "tipo": "FUNDOS"},
        {"ticker": "HGLG11.SA", "nome": "CSHG Logística FII", 
         "tipo": "FUNDOS"},
        {"ticker": "BTC-USD", "nome": "Bitcoin USD", "tipo": "CRIPTO"},
        {"ticker": "ETH-USD", "nome": "Ethereum USD", "tipo": "CRIPTO"},
        {"ticker": "USDBRL=X", "nome": "Dólar Americano", "tipo": "MOEDA"},
    ]

    @staticmethod
    def search_assets(query):
        query = query.upper()
        return [
            asset for asset in MarketDataService.POPULAR_ASSETS 
            if query in asset['ticker'] or query in asset['nome'].upper()
        ]

    @staticmethod
    def get_latest_price(ticker):
        try:
            ticker_obj = yf.Ticker(ticker)
            preco = ticker_obj.fast_info.last_price
            
            if not preco:
                hist = ticker_obj.history(period="1d")
                if not hist.empty:
                    preco = hist['Close'].iloc[-1]
            
            return round(preco, 2) if preco else None
        except Exception:
            return None

    @staticmethod
    def validar_ticker(ticker):
        try:
            ticker_busca = ticker.upper()
            if not ticker_busca.endswith('.SA') and not ('-' in ticker_busca):
                ticker_busca += '.SA'

            ativo = yf.Ticker(ticker_busca)
            
            hist = ativo.history(period="1d")
            
            if hist.empty:
                return None
            
            return round(float(hist['Close'].iloc[-1]), 2)
            
        except Exception as e:
            print(f"Erro ao buscar ticker {ticker}: {e}")
            return None

    @staticmethod
    def get_cotacao_atual(ticker):
        return MarketDataService.validar_ticker(ticker)
    
    @staticmethod
    def _normalizar_tickers(tickers):
        """
        Garante que tickers da B3 tenham .SA e remove duplicatas.
        """
        lista_limpa = []
        for t in tickers:
            t = t.upper().strip()
            if '.' not in t and '-' not in t:
                t += '.SA'
            lista_limpa.append(t)
        return list(set(lista_limpa))

    @staticmethod
    def get_historico_carteira(tickers, periodo="1y"):
        if not tickers:
            return pd.DataFrame()

        tickers_formatados = MarketDataService._normalizar_tickers(tickers)
        print(f"--- Baixando dados para: {tickers_formatados} ---")
        
        try:
            dados = yf.download(
                tickers_formatados, 
                period=periodo, 
                auto_adjust=False, 
                progress=False,
                threads=True
            )

            if dados.empty:  # type: ignore
                print("--- YFinance retornou vazio ---")
                return pd.DataFrame()

            df_fechamento = pd.DataFrame()

            if isinstance(dados.columns, pd.MultiIndex):  # type: ignore
                try:
                    
                    if 'Adj Close' \
                         in dados.columns.get_level_values(0):  # type: ignore
                        df_fechamento = dados['Adj Close']  # type: ignore
                    elif 'Close' \
                            in \
                            dados.columns.get_level_values(0):  # type: ignore
                        df_fechamento = dados['Close']  # type: ignore
                except Exception as e:
                    print(f"Erro extraindo MultiIndex: {e}")

            else:
                coluna = 'Adj Close' if 'Adj Close' \
                    in dados.columns else 'Close'  # type: ignore
                if coluna in dados.columns:  # type: ignore
                    ticker_nome = tickers_formatados[0]
                    df_fechamento = pd.DataFrame(
                        {ticker_nome: dados[coluna]})  # type: ignore

            df_fechamento = df_fechamento.ffill().bfill().fillna(0)

            return df_fechamento

        except Exception as e:
            print(f"Erro crítico no yfinance: {e}")
            return pd.DataFrame()
        
    @staticmethod
    def get_historico_benchmark(benchmark="^BVSP", periodo="1y"):
        """
        Baixa o histórico do índice de referência (Ibovespa, S&P500).
        """
        try:
            ativo = yf.Ticker(benchmark)
            hist = ativo.history(period=periodo)
            
            if hist.empty:
                return pd.Series(dtype='float64')
            
            # Retorna apenas a serie de preços ajustados
            serie = hist['Close']
            serie.index = serie.index.tz_localize(None)  # type: ignore
            
            return serie
            
        except Exception as e:
            print(f"Erro ao baixar benchmark {benchmark}: {e}")
            return pd.Series(dtype='float64')