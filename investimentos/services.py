import yfinance as yf


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