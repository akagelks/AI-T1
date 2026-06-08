import ccxt
import pandas as pd
import streamlit as st

@st.cache_data(ttl=60)
def buscar_dados(symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
    """Busca dados OHLCV da Bybit (evita bloqueios regionais da Binance)."""
    try:
        exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        
        if not ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df.set_index('time', inplace=True)
        return df
        
    except Exception as e:
        st.error(f"Erro ao conectar na API: {str(e)}")
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])