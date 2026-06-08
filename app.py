import sys
import os
# Força o Python a olhar na mesma pasta do app.py para achar a pasta 'src'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from src.data_fetcher import buscar_dados
from src.strategies import ESTRATEGIAS, adicionar_filtro_regime
from src.backtester import rodar_backtest

# ==========================================
# CSS DARK MODE ESTILO BITGET
# ==========================================
st.set_page_config(page_title="AI-T1 Quant Panel", layout="wide", page_icon="📊")

st.markdown("""
<style>
    .stApp {
        background-color: #0b0e11;
        color: #eaecef;
    }
    .metric-card {
        background-color: #1e2329;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #2b3139;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: bold;
        color: #0ecb81;
    }
    .kpi-label {
        font-size: 12px;
        color: #848e9c;
        text-transform: uppercase;
    }
    .strategy-card {
        background-color: #1e2329;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #0ecb81;
        margin-bottom: 10px;
    }
    .strategy-card.short {
        border-left-color: #f6465d;
    }
    div[data-testid="stMetricValue"] {
        color: #0ecb81;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("⚙️ Configurações")
symbol = st.sidebar.selectbox("Ativo", ["BTC/USDT", "ETH/USDT", "SOL/USDT"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h"], index=0)
capital_simulado = st.sidebar.number_input("Capital (USDT)", min_value=100.0, value=1000.0, step=100.0)
filtro_regime = st.sidebar.checkbox("Aplicar Filtro de Regime (EMA 200)", value=True)

# ==========================================
# BUSCA DADOS
# ==========================================
with st.spinner("Carregando dados..."):
    df = buscar_dados(symbol, timeframe, limit=500)

if df.empty:
    st.error("Erro ao carregar dados. Tente novamente.")
    st.stop()

df = adicionar_filtro_regime(df)

# ==========================================
# HEADER
# ==========================================
st.title("📊 AI-T1 Quant Panel")
st.markdown(f"**{symbol}** | Timeframe: {timeframe} | Capital: ${capital_simulado:,.2f}")

# ==========================================
# ABAS
# ==========================================
tab1, tab2, tab3 = st.tabs([" Overview", "🧪 Backtest", "🤖 Estratégias Ativas"])

# ==========================================
# ABA 1: OVERVIEW (Estilo Bitget)
# ==========================================
with tab1:
    st.subheader("Visão Geral do Mercado")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Preço Atual", f"${df['close'].iloc[-1]:,.2f}")
    var_24h = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0
    col2.metric("Variação 24h", f"{var_24h:.2f}%")
    col3.metric("Volume", f"{df['volume'].iloc[-1]:,.0f}")
    col4.metric("EMA 200", f"${df['ema_200'].iloc[-1]:,.2f}")
    
    # Gráfico Candlestick
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Preço', increasing_line_color='#0ecb81', decreasing_line_color='#f6465d'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['ema_200'], name='EMA 200',
        line=dict(color='#f0b90b', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        x=df.index, y=df['volume'], name='Volume',
        marker_color=np.where(df['close'] > df['open'], '#0ecb81', '#f6465d')
    ), row=2, col=1)
    
    fig.update_layout(
        template='plotly_dark',
        height=500,
        xaxis_rangeslider_visible=False,
        paper_bgcolor='#0b0e11',
        plot_bgcolor='#0b0e11'
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# ABA 2: BACKTEST (Métricas Institucionais)
# ==========================================
with tab2:
    st.subheader("Simulador de Estratégia")
    
    estrategia_sel = st.selectbox(
        "Escolha a estratégia:",
        options=list(ESTRATEGIAS.keys()),
        format_func=lambda x: f"{ESTRATEGIAS[x]['icone']} {x}"
    )
    
    if st.button(" Rodar Backtest", type="primary"):
        with st.spinner("Processando..."):
            resultado = rodar_backtest(df, estrategia_sel, capital_simulado, filtro_regime)
        
        metricas = resultado['metricas']
        trades = resultado['trades']
        equity = resultado['equity']
        
        # KPIs estilo Bitget
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-label">ROI</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-value">{metricas["roi_pct"]:.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-label">Win Rate</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-value">{metricas["win_rate"]:.1f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-label">Profit Factor</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-value">{metricas["profit_factor"]:.2f}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-label">Max Drawdown</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-value" style="color:#f6465d">{metricas["max_drawdown_pct"]:.2f}%</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col5:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-label">Total Trades</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-value">{metricas["total_trades"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Curva de Patrimônio
        st.markdown("### 📈 Curva de Patrimônio")
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=list(range(len(equity))),
            y=equity,
            mode='lines',
            name='Patrimônio',
            line=dict(color='#0ecb81', width=3)
        ))
        fig_equity.add_hline(y=capital_simulado, line_dash="dash", line_color="#848e9c", 
                             annotation_text="Capital Inicial")
        fig_equity.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor='#0b0e11',
            plot_bgcolor='#0b0e11',
            xaxis_title="Número do Trade",
            yaxis_title="Capital (USDT)"
        )
        st.plotly_chart(fig_equity, use_container_width=True)
        
        # Tabela Detalhada de Trades (Estilo Bitget)
        if trades:
            st.markdown("### 📋 Histórico de Operações")
            df_trades = pd.DataFrame(trades)
            display_df = df_trades[[
                'timestamp_entrada', 'tipo', 'preco_entrada', 
                'timestamp_saida', 'preco_saida', 'resultado', 'pnl_liquido'
            ]].copy()
            display_df.columns = [
                'Abertura', 'Direção', 'Preço Entrada',
                'Fechamento', 'Preço Saída', 'Resultado', 'PnL (USDT)'
            ]
            display_df['PnL (USDT)'] = display_df['PnL (USDT)'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(display_df, use_container_width=True)

# ==========================================
# ABA 3: ESTRATÉGIAS ATIVAS (Estilo Copy Trade)
# ==========================================
with tab3:
    st.subheader("Central de Estratégias")
    st.markdown("Ative ou desative estratégias para operar em tempo real (simulação).")
    
    estrategias_ativas = []
    
    for nome, dados in ESTRATEGIAS.items():
        # Card da estratégia
        css_class = "strategy-card short" if dados['tipo'] == 'SHORT' else "strategy-card"
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{dados['icone']} {nome}**")
            st.caption(f"{dados['descricao']} | TP: {dados['tp_pct']}% | SL: {dados['sl_pct']}%")
        
        with col2:
            st.markdown(f"**Tipo:** {dados['tipo']}")
        
        with col3:
            ativo = st.toggle("Ativar", key=f"toggle_{nome}")
            if ativo:
                estrategias_ativas.append(nome)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Status do Bot
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Estratégias Ativas", len(estrategias_ativas))
    with col2:
        st.metric("Status", "🟢 OPERANDO" if estrategias_ativas else "⏸️ PAUSADO")
    
    if estrategias_ativas:
        st.success(f"✅ Estratégias ativas: {', '.join(estrategias_ativas)}")
        st.info("""
         **Próximo passo:** Para operar com dinheiro real, configure as API Keys 
        no Streamlit Secrets e migre para um VPS 24/7.
        """)
    else:
        st.warning("⚠️ Nenhuma estratégia ativa. Ative pelo menos uma para começar.")