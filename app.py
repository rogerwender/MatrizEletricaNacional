import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# 1. CONFIGURAÇÕES GERAIS DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="RealEstate Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

CORES = {
    "fundo": "#0B1120",
    "painel": "#121C2E",
    "borda": "#26364D",
    "texto": "#F4F7FB",
    "texto_secundario": "#A9B8CC",
    "destaque_principal": "#3B82F6", # Azul moderno
    "destaque_secundario": "#8B5CF6", # Roxo
    "alerta": "#F59E0B",
}

# =========================================================
# 2. ESTILO VISUAL PERSONALIZADO
# =========================================================

def aplicar_estilo():
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: dark; }}
        .stApp {{ background: {CORES["fundo"]}; color: {CORES["texto"]}; }}
        .block-container {{ max-width: 1550px; padding-top: 1.1rem; padding-bottom: 2.5rem; }}
        [data-testid="stHeader"] {{ background: rgba(11, 17, 32, 0.85); }}
        [data-testid="stSidebar"] {{ background: {CORES["painel"]}; border-right: 1px solid {CORES["borda"]}; }}
        
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {{ color: #FFFFFF !important; }}
        h1, h2, h3, h4, p, label {{ color: {CORES["texto"]}; }}
        
        [data-testid="stMetric"] {{
            background: linear-gradient(145deg, #162238, #111B2C);
            border: 1px solid {CORES["borda"]};
            padding: 17px 18px;
            border-radius: 15px;
        }}
        [data-testid="stMetricLabel"] p {{ color: {CORES["texto_secundario"]} !important; font-size: 0.84rem; }}
        [data-testid="stMetricValue"] {{ color: {CORES["texto"]} !important; font-weight: 700; }}
        
        [data-testid="stPlotlyChart"] {{
            background: {CORES["painel"]};
            border: 1px solid {CORES["borda"]};
            border-radius: 15px;
            padding: 7px;
        }}
        
        .hero {{
            background: radial-gradient(circle at 90% 0%, rgba(59,130,246,0.15), transparent 35%),
                        linear-gradient(120deg, #15243A, #0D1626);
            border: 1px solid #1D2D44;
            border-radius: 18px;
            padding: 22px 26px;
            margin-bottom: 20px;
        }}
        .hero-eyebrow {{ color: {CORES["destaque_principal"]}; text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.72rem; font-weight: 700; }}
        .hero-title {{ color: #FFFFFF; font-size: clamp(1.65rem, 3vw, 2.25rem); font-weight: 800; margin: 0; }}
        .hero-subtitle {{ color: #A9B8CC; font-size: 0.94rem; margin-top: 6px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def estilizar_grafico(fig, altura: int = 380):
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        paper_bgcolor=CORES["painel"],
        plot_bgcolor=CORES["painel"],
        font=dict(family="Arial, sans-serif", size=12, color=CORES["texto"]),
        margin=dict(l=18, r=18, t=50, b=20),
        legend=dict(font=dict(color=CORES["texto_secundario"]), bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="rgba(169,184,204,0.10)", showline=False)
    fig.update_yaxes(gridcolor="rgba(169,184,204,0.10)", showline=False)
    return fig

# =========================================================
# 3. CARREGAMENTO DOS DADOS (CONEXÃO SQLITE)
# =========================================================

@st.cache_data(show_spinner=False)
def carregar_dados():
    """Conecta no arquivo local imoveis.db e extrai os dados."""
    try:
        with sqlite3.connect('imoveis.db') as conn:
            query = """
                SELECT 
                    bairro, 
                    tipo_imovel, 
                    area_m2, 
                    preco_aluguel, 
                    valor_condominio,
                    (preco_aluguel / NULLIF(area_m2, 0)) AS preco_m2,
                    latitude, 
                    longitude 
                FROM imoveis_locacao
            """
            df = pd.read_sql(query, conn)
            return df
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados imoveis.db: {e}")
        return pd.DataFrame()

# =========================================================
# 4. RENDERIZAÇÃO DA APLICAÇÃO
# =========================================================

aplicar_estilo()
dados = carregar_dados()

if dados.empty:
    st.error("Banco de dados vazio ou não encontrado. Verifique se o arquivo imoveis.db está na mesma pasta.")
    st.stop()

# Sidebar
st.sidebar.markdown("## 🏢 RealEstate")
st.sidebar.caption("MARKET INTELLIGENCE")
st.sidebar.divider()

pagina = st.sidebar.radio(
    "Navegação",
    ["Visão Geral", "Mapeamento Espacial", "Análise de Distribuição"],
    format_func=lambda item: {
        "Visão Geral": "📊  Visão Geral",
        "Mapeamento Espacial": "🗺️  Mapeamento Espacial",
        "Análise de Distribuição": "📈  Análise de Preços",
    }[item],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.markdown("### Filtros Analíticos")

bairros_disponiveis = sorted(dados["bairro"].unique())
tipos_disponiveis = sorted(dados["tipo_imovel"].unique())

bairro_selecionado = st.sidebar.multiselect("Regiões", bairros_disponiveis, default=bairros_disponiveis)
tipo_selecionado = st.sidebar.multiselect("Tipologia", tipos_disponiveis, default=tipos_disponiveis)

# Aplicar filtros
df_filtrado = dados[
    (dados["bairro"].isin(bairro_selecionado)) & 
    (dados["tipo_imovel"].isin(tipo_selecionado))
]

st.sidebar.divider()
st.sidebar.markdown("### ⚙️ Engine")
st.sidebar.caption("Data: SQLite | Viz: Plotly")

# Header Hero
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-eyebrow">Painel Analytics · Inteligência Imobiliária</div>
        <div class="hero-title">Brasília Real Estate Dashboard</div>
        <div class="hero-subtitle">
            Análise de Locação para Imóveis Compactos &nbsp;·&nbsp; Total Filtrado: {len(df_filtrado)} imóveis
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()


# =========================================================
# PÁGINA 1: VISÃO GERAL
# =========================================================
if pagina == "Visão Geral":
    st.markdown("### Indicadores Chave de Mercado")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Ticket Médio (Aluguel)", f"R$ {df_filtrado['preco_aluguel'].mean():.2f}")
    with col2:
        st.metric("📏 Preço Médio / m²", f"R$ {df_filtrado['preco_m2'].mean():.2f}")
    with col3:
        st.metric("🏢 Condomínio Médio", f"R$ {df_filtrado['valor_condominio'].mean():.2f}")
    with col4:
        st.metric("📐 Área Média", f"{df_filtrado['area_m2'].mean():.1f} m²")

    st.markdown("---")
    
    col_graf1, col_graf2 = st.columns([1, 1])
    
    with col_graf1:
        st.markdown("#### Preço Médio por Região")
        df_agrupado = df_filtrado.groupby("bairro", as_index=False)["preco_aluguel"].mean()
        fig_bar = px.bar(
            df_agrupado.sort_values("preco_aluguel", ascending=True),
            x="preco_aluguel",
            y="bairro",
            orientation="h",
            color="preco_aluguel",
            color_continuous_scale=[CORES["painel"], CORES["destaque_principal"]]
        )
        fig_bar.update_layout(coloraxis_showscale=False)
        st.plotly_chart(estilizar_grafico(fig_bar), use_container_width=True)

    with col_graf2:
        st.markdown("#### Composição por Tipologia")
        df_tipos = df_filtrado["tipo_imovel"].value_counts().reset_index()
        df_tipos.columns = ["Tipo", "Quantidade"]
        fig_pie = px.pie(
            df_tipos,
            names="Tipo",
            values="Quantidade",
            hole=0.6,
            color_discrete_sequence=[CORES["destaque_principal"], CORES["destaque_secundario"]]
        )
        st.plotly_chart(estilizar_grafico(fig_pie), use_container_width=True)


# =========================================================
# PÁGINA 2: MAPEAMENTO ESPACIAL
# =========================================================
elif pagina == "Mapeamento Espacial":
    st.markdown("### Distribuição Geográfica e Calor de Preços")
    
    fig_map = px.scatter_mapbox(
        df_filtrado, 
        lat="latitude", 
        lon="longitude", 
        color="preco_m2", 
        size="preco_aluguel",
        hover_name="bairro", 
        hover_data={"latitude": False, "longitude": False, "tipo_imovel": True, "area_m2": True},
        color_continuous_scale=px.colors.sequential.Plasma, 
        size_max=15, 
        zoom=11,
        mapbox_style="carto-darkmatter" # Estilo de mapa escuro para combinar com o tema
    )
    st.plotly_chart(estilizar_grafico(fig_map, altura=600), use_container_width=True)


# =========================================================
# PÁGINA 3: ANÁLISE DE DISTRIBUIÇÃO
# =========================================================
elif pagina == "Análise de Distribuição":
    st.markdown("### Dispersão e Outliers de Mercado")
    
    col_box1, col_box2 = st.columns(2)
    
    with col_box1:
        fig_box1 = px.box(
            df_filtrado, 
            x="bairro", 
            y="preco_aluguel", 
            color="tipo_imovel",
            title="Distribuição do Valor de Aluguel Bruto",
            color_discrete_sequence=[CORES["destaque_principal"], CORES["destaque_secundario"]]
        )
        st.plotly_chart(estilizar_grafico(fig_box1), use_container_width=True)
        
    with col_box2:
        fig_box2 = px.box(
            df_filtrado, 
            x="bairro", 
            y="preco_m2", 
            color="tipo_imovel",
            title="Distribuição do Custo por Metro Quadrado",
            color_discrete_sequence=[CORES["destaque_principal"], CORES["destaque_secundario"]]
        )
        st.plotly_chart(estilizar_grafico(fig_box2), use_container_width=True)

# Rodapé
st.divider()
st.caption("Desenvolvido por Rogerio Wender Tavares | Engenharia de Dados & Analytics BB")
