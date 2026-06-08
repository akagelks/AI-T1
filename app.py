import streamlit as st
import pandas as pd
import ccxt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Quant Copy Panel", layout="wide", page_icon="📊")

# ==========================================
# SIDEBAR - CONTROLES GLOBAIS
# ==========================================
st.sidebar.title("⚙️ Controles")
symbol = st.sidebar.selectbox("Ativo", ["BTC/USDT", "ETH/USDT", "SOL/USDT"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h"], index=0)
capital_simulado = st.sidebar.number_input("Capital para Simulação (USDT)", min_value=10.0, value=100.0, step=10.0)

# ==========================================
# ESTRATÉGIAS DISPONÍVEIS (Estilo Copy Trade)
# ==========================================
ESTRATEGIAS = {
    "Buy-the-Dip Scalp": {
        "descricao": "Compra em quedas rápidas, TP curto (0.5%), SL controlado (2.5%)",
        "dip_pct": 0.8,
        "lookback": 2,
        "tp_pct": 0.5,
        "sl_pct": 2.5,
        "ativo": True,
        "icone": "📉"
    },
    "Volume Spike Reversal": {
        "descricao": "Detecta volume anômalo (Z-Score > 2) e opera reversão",
        "zscore_threshold": 2.0,
        "tp_pct": 0.8,
        "sl_pct": 1.5,
        "ativo": False,
        "icone": "📊"
    },
    "Breakout Momentum": {
        "descricao": "Compra rompimento de máxima de 20 períodos com volume",
        "lookback_high": 20,
        "vol_multiplier": 1.5,
        "tp_pct": 1.2,
        "sl_pct": 2.0,
        "ativo": False,
        "icone": "🚀"
    }
}

# ==========================================
# MOTOR DE DADOS (CCXT - BYBIT)
# ==========================================
@st.cache_data(ttl=60)
def buscar_dados(symbol, timeframe, limit=500):
    try:
        # Usando Bybit para evitar bloqueios regionais da Binance no Streamlit Cloud
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

# ==========================================
# MOTOR DE BACKTEST (Simula a estratégia)
# ==========================================
def rodar_backtest(df, estrategia, capital_inicial):
    trades = []
    capital = capital_inicial
    posicao_aberta = False
    
    params = ESTRATEGIAS[estrategia]
    
    for i in range(params.get('lookback', params.get('lookback_high', 20)), len(df)):
        janela = df.iloc[i-params.get('lookback', params.get('lookback_high', 20)):i]
        candle_atual = df.iloc[i]
        
        sinal_compra = False
        
        if estrategia == "Buy-the-Dip Scalp":
            queda_pct = ((janela['close'].iloc[-1] - candle_atual['close']) / janela['close'].iloc[-1]) * 100
            if queda_pct >= params['dip_pct']:
                sinal_compra = True
                
        elif estrategia == "Volume Spike Reversal":
            vol_media = janela['volume'].mean()
            vol_std = janela['volume'].std()
            z_score = (candle_atual['volume'] - vol_media) / vol_std if vol_std > 0 else 0
            if z_score > params['zscore_threshold'] and candle_atual['close'] < candle_atual['open']:
                sinal_compra = True
                
        elif estrategia == "Breakout Momentum":
            maxima = janela['high'].max()
            vol_media = janela['volume'].mean()
            if candle_atual['close'] > maxima and candle_atual['volume'] > vol_media * params['vol_multiplier']:
                sinal_compra = True
        
        if sinal_compra and not posicao_aberta:
            preco_entrada = candle_atual['close']
            tp = preco_entrada * (1 + params['tp_pct']/100)
            sl = preco_entrada * (1 - params['sl_pct']/100)
            tamanho_posicao = capital * 0.95
            quantidade = tamanho_posicao / preco_entrada
            taxa_entrada = tamanho_posicao * 0.001
            
            posicao_aberta = True
            trade = {
                'entrada_time': df.index[i],
                'entrada_preco': preco_entrada,
                'tp': tp,
                'sl': sl,
                'quantidade': quantidade,
                'taxa_entrada': taxa_entrada,
                'status': 'ABERTO'
            }
        
        if posicao_aberta:
            resultado = None
            preco_saida = None
            
            if candle_atual['high'] >= tp:
                resultado = 'WIN'
                preco_saida = tp
            elif candle_atual['low'] <= sl:
                resultado = 'LOSS'
                preco_saida = sl
            
            if resultado:
                valor_saida = trade['quantidade'] * preco_saida
                taxa_saida = valor_saida * 0.001
                pnl_bruto = valor_saida - (trade['quantidade'] * trade['entrada_preco'])
                pnl_liquido = pnl_bruto - trade['taxa_entrada'] - taxa_saida
                
                capital += pnl_liquido
                trade['saida_time'] = df.index[i]
                trade['saida_preco'] = preco_saida
                trade['resultado'] = resultado
                trade['pnl'] = pnl_liquido
                trade['capital_final'] = capital
                trades.append(trade)
                posicao_aberta = False
    
    return trades, capital

# ==========================================
# BUSCA OS DADOS E VERIFICA ERROS
# ==========================================
with st.spinner("Buscando dados reais da Bybit..."):
    df = buscar_dados(symbol, timeframe)

# TRAVA DE SEGURANÇA: Se não houver dados, para o app aqui para não dar erro de índice
if df.empty:
    st.stop()

# ==========================================
# LAYOUT PRINCIPAL - 3 ABAS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Mercado Atual", "📈 Simulador / Backtest", "🤖 Bot Live (Copy Trade)"])

# ==========================================
# ABA 1: MERCADO ATUAL
# ==========================================
with tab1:
    st.header(f"📊 {symbol} - Visão em Tempo Real")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Preço Atual", f"${df['close'].iloc[-1]:,.2f}")
    variacao_24h = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0
    col2.metric("Variação 24h", f"{variacao_24h:.2f}%", delta=f"{variacao_24h:.2f}%")
    col3.metric("Volume (última vela)", f"{df['volume'].iloc[-1]:,.0f}")
    col4.metric("Média Volume (20)", f"{df['volume'].tail(20).mean():,.0f}")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Preço'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], name='Volume', 
                         marker_color=np.where(df['close'] > df['open'], 'green', 'red')), 
                  row=2, col=1)
    
    fig.update_layout(height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 Vá para a aba **📈 Simulador / Backtest** para testar estratégias com dados reais.")

# ==========================================
# ABA 2: SIMULADOR / BACKTEST
# ==========================================
with tab2:
    st.header("📈 Simulador de Estratégias (Backtest)")
    st.markdown(f"**Capital inicial:** US$ {capital_simulado:,.2f} | **Período:** Últimos {len(df)} candles ({timeframe})")
    
    estrategia_selecionada = st.selectbox(
        "Escolha a estratégia para simular:",
        options=list(ESTRATEGIAS.keys()),
        format_func=lambda x: f"{ESTRATEGIAS[x]['icone']} {x}"
    )
    
    st.markdown(f"**Como funciona:** {ESTRATEGIAS[estrategia_selecionada]['descricao']}")
    
    if st.button("🚀 Rodar Simulação Agora", type="primary"):
        with st.spinner("Processando backtest..."):
            trades, capital_final = rodar_backtest(df, estrategia_selecionada, capital_simulado)
        
        if not trades:
            st.warning("⚠️ Nenhum trade foi gerado neste período. Tente outro timeframe ou estratégia.")
        else:
            df_trades = pd.DataFrame(trades)
            wins = len(df_trades[df_trades['resultado'] == 'WIN'])
            losses = len(df_trades[df_trades['resultado'] == 'LOSS'])
            win_rate = (wins / len(df_trades)) * 100
            lucro_total = capital_final - capital_simulado
            roi = (lucro_total / capital_simulado) * 100
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Trades Totais", len(df_trades))
            col2.metric("Win Rate", f"{win_rate:.1f}%", delta=f"{wins}W / {losses}L")
            col3.metric("Lucro Líquido", f"US$ {lucro_total:,.2f}", delta=f"{roi:.2f}%")
            col4.metric("Capital Final", f"US$ {capital_final:,.2f}")
            col5.metric("Maior Gain", f"US$ {df_trades['pnl'].max():,.2f}" if 'pnl' in df_trades else "N/A")
            
            fig_capital = go.Figure()
            fig_capital.add_trace(go.Scatter(
                x=df_trades['saida_time'],
                y=df_trades['capital_final'],
                mode='lines+markers',
                name='Curva de Capital',
                line=dict(color='gold', width=3)
            ))
            fig_capital.add_hline(y=capital_simulado, line_dash="dash", line_color="gray", 
                                  annotation_text="Capital Inicial")
            fig_capital.update_layout(
                title="📈 Evolução do Capital (Simulação)",
                xaxis_title="Data/Hora",
                yaxis_title="Capital (USDT)",
                height=400
            )
            st.plotly_chart(fig_capital, use_container_width=True)
            
            st.subheader("📋 Histórico Detalhado de Trades")
            display_df = df_trades[['entrada_time', 'entrada_preco', 'saida_time', 'saida_preco', 'resultado', 'pnl']].copy()
            display_df.columns = ['Entrada', 'Preço Entrada', 'Saída', 'Preço Saída', 'Resultado', 'P&L (USDT)']
            display_df['P&L (USDT)'] = display_df['P&L (USDT)'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(display_df, use_container_width=True)
            
            st.warning("⚠️ **Atenção:** Esta é uma simulação histórica. Resultados passados não garantem resultados futuros. Taxas de 0.1% (taker) foram descontadas.")

# ==========================================
# ABA 3: BOT LIVE (COPY TRADE)
# ==========================================
with tab3:
    st.header("🤖 Painel de Controle - Bot Live")
    
    st.markdown("""
    ### Como funciona o Copy Trade?
    1. **Selecione** as estratégias que você quer operar
    2. **Valide** no simulador (aba anterior) se a estratégia funciona
    3. **Ative** o bot abaixo para começar a operar em tempo real
    4. **Monitore** os trades sendo executados automaticamente
    """)
    
    st.divider()
    
    st.subheader("📋 Estratégias Disponíveis")
    
    estrategias_ativas = []
    for nome, dados in ESTRATEGIAS.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{dados['icone']} {nome}**")
            st.caption(dados['descricao'])
        with col2:
            ativo = st.toggle("Ativar", key=f"toggle_{nome}", value=dados['ativo'])
            if ativo:
                estrategias_ativas.append(nome)
    
    st.divider()
    
    st.subheader("🔴 Status do Bot")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Estratégias Ativas", len(estrategias_ativas))
    with col2:
        st.metric("Status", "⏸️ PAUSADO" if not st.session_state.get('bot_ativo', False) else "🟢 OPERANDO")
    
    if not st.session_state.get('bot_ativo', False):
        if st.button("▶️ ATIVAR BOT EM TEMPO REAL", type="primary", use_container_width=True):
            if not estrategias_ativas:
                st.error("❌ Selecione pelo menos uma estratégia antes de ativar!")
            else:
                st.session_state['bot_ativo'] = True
                st.session_state['estrategias_ativas'] = estrategias_ativas
                st.rerun()
    else:
        if st.button("⏸️ PAUSAR BOT", type="secondary", use_container_width=True):
            st.session_state['bot_ativo'] = False
            st.rerun()
    
    if st.session_state.get('bot_ativo', False):
        st.success(f"✅ **Bot ATIVO!** Operando com: {', '.join(st.session_state.get('estrategias_ativas', []))}")
        st.info("""
        🔧 **Próximo passo técnico:** Para o bot operar de verdade, precisamos:
        1. Configurar suas **API Keys** da Bybit/Binance (modo Trade-Only, SEM permissão de saque)
        2. Rodar este código em um **VPS 24/7** (Streamlit Cloud adormece quando você fecha a aba)
        3. Me avise quando quiser configurar isso - te guio passo a passo.
        """)
    else:
        st.warning("""
        ⚠️ **Modo Simulação Atual:** O bot está apenas mostrando o painel. 
        Para operar com dinheiro real, você precisa configurar as API Keys e um VPS.
        """)