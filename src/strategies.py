import pandas as pd
import numpy as np

# ==========================================
# DEFINIÇÃO DAS ESTRATÉGIAS
# ==========================================
ESTRATEGIAS = {
    "Buy-the-Dip Scalp": {
        "descricao": "Compra em quedas rápidas com reversão à média",
        "dip_pct": 0.8,
        "lookback": 2,
        "tp_pct": 1.5,
        "sl_pct": 2.5,
        "icone": "📉",
        "tipo": "LONG"
    },
    "Volume Spike Reversal": {
        "descricao": "Detecta absorção institucional (volume anômalo + queda)",
        "zscore_threshold": 2.5,
        "tp_pct": 1.2,
        "sl_pct": 1.8,
        "icone": "📊",
        "tipo": "LONG"
    },
    "Breakout Momentum": {
        "descricao": "Rompimento de máxima com volume acima da média",
        "lookback_high": 20,
        "vol_multiplier": 1.5,
        "tp_pct": 2.0,
        "sl_pct": 1.5,
        "icone": "🚀",
        "tipo": "LONG"
    },
    "Short Rejection": {
        "descricao": "Short em rejeição de topo com volume",
        "zscore_threshold": 2.0,
        "tp_pct": 1.0,
        "sl_pct": 1.5,
        "icone": "⬇️",
        "tipo": "SHORT"
    }
}

# ==========================================
# FILTRO DE REGIME (EMA 200)
# ==========================================
def adicionar_filtro_regime(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona EMA 200 para filtrar tendência macro."""
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['acima_ema'] = df['close'] > df['ema_200']
    return df

# ==========================================
# GERADOR DE SINAIS
# ==========================================
def gerar_sinais(df: pd.DataFrame, nome_estrategia: str) -> pd.Series:
    """Retorna uma Series booleana com True onde há sinal de entrada."""
    params = ESTRATEGIAS[nome_estrategia]
    sinais = pd.Series(False, index=df.index)
    
    if nome_estrategia == "Buy-the-Dip Scalp":
        queda = df['close'].pct_change(periods=params['lookback']) * 100
        sinais = queda <= -params['dip_pct']
        
    elif nome_estrategia == "Volume Spike Reversal":
        vol_media = df['volume'].rolling(20).mean()
        vol_std = df['volume'].rolling(20).std()
        z_score = (df['volume'] - vol_media) / vol_std
        sinais = (z_score > params['zscore_threshold']) & (df['close'] < df['open'])
        
    elif nome_estrategia == "Breakout Momentum":
        maxima = df['high'].rolling(params['lookback_high']).max()
        vol_media = df['volume'].rolling(20).mean()
        sinais = (df['close'] > maxima.shift(1)) & (df['volume'] > vol_media * params['vol_multiplier'])
        
    elif nome_estrategia == "Short Rejection":
        vol_media = df['volume'].rolling(20).mean()
        vol_std = df['volume'].rolling(20).std()
        z_score = (df['volume'] - vol_media) / vol_std
        # Short: volume alto + candle de rejeição (close < open) + preço acima da EMA
        if 'acima_ema' in df.columns:
            sinais = (z_score > params['zscore_threshold']) & (df['close'] < df['open']) & df['acima_ema']
        else:
            sinais = (z_score > params['zscore_threshold']) & (df['close'] < df['open'])
    
    return sinais   