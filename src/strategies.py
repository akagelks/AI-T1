import numpy as np
import pandas as pd

ESTRATEGIAS = {
    "Buy-the-Dip Scalp": {"dip_pct": 0.8, "lookback": 2, "tp_pct": 0.5, "sl_pct": 2.5},
    "Volume Spike Reversal": {"zscore_threshold": 2.0, "tp_pct": 0.8, "sl_pct": 1.5},
    "Breakout Momentum": {"lookback_high": 20, "vol_multiplier": 1.5, "tp_pct": 1.2, "sl_pct": 2.0}
}

def aplicar_logica(df, nome_estrategia):
    params = ESTRATEGIAS[nome_estrategia]
    df_copy = df.copy()
    
    # Lógica simplificada para exemplo
    if nome_estrategia == "Buy-the-Dip Scalp":
        df_copy['queda'] = df_copy['close'].pct_change(params['lookback']) * 100
        df_copy['sinal'] = df_copy['queda'] <= -params['dip_pct']
        
    elif nome_estrategia == "Volume Spike Reversal":
        vol_ma = df_copy['volume'].rolling(20).mean()
        vol_std = df_copy['volume'].rolling(20).std()
        z_score = (df_copy['volume'] - vol_ma) / vol_std
        df_copy['sinal'] = (z_score > params['zscore_threshold']) & (df_copy['close'] < df_copy['open'])
        
    else: # Breakout
        maxima = df_copy['high'].rolling(params['lookback_high']).max()
        df_copy['sinal'] = (df_copy['close'] > maxima) & (df_copy['volume'] > df_copy['volume'].rolling(20).mean() * params['vol_multiplier'])
        
    return df_copy