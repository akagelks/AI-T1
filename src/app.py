import streamlit as st
from src.data_fetcher import buscar_dados_bybit
from src.strategies import calcular_sinal_dip
from src.backtester import rodar_simulacao

# --- LAYOUT ---
st.title("Quant Dashboard")
df = buscar_dados_bybit("BTC/USDT")
df_com_sinais = calcular_sinal_dip(df)

# Mostra o gráfico
st.line_chart(df_com_sinais['close'])