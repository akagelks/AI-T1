import pandas as pd
import numpy as np

def calcular_sinal_dip(df, dip_pct=0.8, lookback=2):
    """Calcula se houve um dip significativo baseado nos parâmetros."""
    df['queda_pct'] = df['close'].pct_change(periods=lookback) * 100
    df['sinal'] = np.where(df['queda_pct'] <= -dip_pct, True, False)
    return df