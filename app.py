import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# =========================================================
# 1. CONFIGURAÇÕES GERAIS DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="CleanEnergy Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CORES = {
    "fundo": "#0B1120",
    "painel": "#121C2E",
    "borda": "#26364D",
    "texto": "#F4F7FB",
    "texto_secundario": "#A9B8CC",
    "verde": "#10B981",  # Renovável / Solar
    "azul": "#3B82F6",   # Eólica / Hidro
    "amarelo": "#F59E0B", # Biomassa / Outros
    "vermelho": "#EF4444",# Fóssil / CO2
    "roxo": "#8B5CF6",
}

URL_OWID_DATASET = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"


# =========================================================
# 2. BANCO DE DADOS: CONTADOR DE VISITAS
# =========================================================

def inicializar_banco():
    """Garante a criação da tabela do contador de acessos."""
    with sqlite3.connect("visitor_counter.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contador (
                id INTEGER PRIMARY KEY,
                visitas_totais INTEGER,
                visitantes_unicos INTEGER
            )
            """
        )
        cursor.execute("SELECT COUNT(*) FROM contador WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO contador (id, visitas_totais, visitantes_unicos) VALUES (1, 0, 0)"
            )
        conn.commit()


def registrar_visita() -> tuple[int, int]:
    """Registra navegações e sessões no banco SQLite de forma atômica."""
    inicializar_banco()
    eh_nova_sessao = False

    if "visitou_energia" not in st.session_state:
        st.session_state["visitou_energia"] = True
        eh_nova_sessao = True

    incremento_unico = 1 if eh_nova_sessao else 0

    with sqlite3.connect("visitor_counter.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE contador
            SET visitas_totais = visitas_totais + 1,
                visitantes_unicos = visitantes_unicos + ?
            WHERE id = 1
            """,
            (incremento_unico,),
        )
        conn.commit()

        cursor.execute("SELECT visitas_totais, visitantes_unicos FROM contador WHERE id = 1")
        resultado = cursor.fetchone()
        return resultado if resultado else (0, 0)


# =========================================================
# 3. ESTILO VISUAL PERSONALIZADO
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
            background: radial-gradient(circle at 90% 0%, rgba(16,185,129,0.18), transparent 35%),
                        linear-gradient(120deg, #15243A, #0D2622);
            border: 1px solid #1B4D3E;
            border-radius: 18px;
            padding: 22px 26px;
            margin-bottom: 20px;
        }}
        .hero-eyebrow {{ color: {CORES["verde"]}; text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.72rem; font-weight: 700; }}
        .hero-title {{ color: #FFFFFF; font-size: clamp(1.65rem, 3vw, 2.25rem); font-weight: 800; margin: 0; }}
        .hero-subtitle {{ color: #FFFFFF; font-size: 0.94rem; margin-top: 6px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 4. CARREGAMENTO E PROCESSAMENTO DOS DADOS
# =========================================================

@st.cache_data(ttl=86400, show_spinner=False)
def carregar_dados_energia() -> pd.DataFrame:
    """Carrega o dataset global de energia da OWID (com cache de 24h)."""
    colunas_interesse = [
        "country", "year", "iso_code", "population", "gdp",
        "primary_energy_consumption", "electricity_generation",
        "renewables_share_elec", "solar_share_elec", "wind_share_elec",
        "hydro_share_elec", "fossil_share_elec", "greenhouse_gas_emissions"
    ]
    try:
        df = pd.read_csv(URL_OWID_DATASET, usecols=lambda c: c in colunas_interesse)
        df = df[df["year"] >= 2000].copy()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados da OWID: {e}")
        return pd.DataFrame()


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
# 5. RENDERIZAÇÃO DA APLICAÇÃO
# =========================================================

aplicar_estilo()
visitas_totais, visitantes_unicos = registrar_visita()

# Sidebar
st.sidebar.markdown("## ⚡ CleanEnergy")
st.sidebar.caption("GLOBAL & LOCAL TRANSITION")
st.sidebar.divider()

pagina = st.sidebar.radio(
    "Navegação",
    ["Visão Geral", "Matriz Elétrica", "Comparador Global"],
    format_func=lambda item: {
        "Visão Geral": "📊  Visão Geral",
        "Matriz Elétrica": "🌱  Matriz Elétrica",
        "Comparador Global": "🌍  Comparador Global",
    }[item],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.markdown("### Filtros")

dados = carregar_dados_energia()

if dados.empty:
    st.error("Não foi possível carregar o dataset de energia.")
    st.stop()

# Lista de países disponíveis
paises = sorted(dados["country"].unique())
pais_padrao_idx = paises.index("Brazil") if "Brazil" in paises else 0

pais_selecionado = st.sidebar.selectbox("País / Região", paises, index=pais_padrao_idx)
ano_selecionado = st.sidebar.slider("Ano de referência", 2000, 2023, 2022)

st.sidebar.divider()

# Métrica do Contador de Visitas
st.sidebar.markdown("### 📈 Métrica do App")
col_vis1, col_vis2 = st.sidebar.columns(2)
col_vis1.metric("Page Views", f"{visitas_totais:,}".replace(",", "."))
col_vis2.metric("Únicos", f"{visitantes_unicos:,}".replace(",", "."))

# Header Hero
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-eyebrow">Painel Analytics · Transição Energética</div>
        <div class="hero-title">Clean Energy Dashboard</div>
        <div class="hero-subtitle">
            Análise para <b>{pais_selecionado}</b> &nbsp;·&nbsp; Ano base {ano_selecionado}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Filtrar dados do país
df_pais = dados[dados["country"] == pais_selecionado].sort_values("year")
df_ano = df_pais[df_pais["year"] == ano_selecionado]


# =========================================================
# PÁGINA 1: VISÃO GERAL
# =========================================================
if pagina == "Visão Geral":
    st.markdown("### Indicadores Chave")
    
    if not df_ano.empty:
        linha_ano = df_ano.iloc[0]
        
        # 1. Puxa os dados brutos da linha
        renovavel_pct = linha_ano.get("renewables_share_elec", 0)
        solar_pct = linha_ano.get("solar_share_elec", 0)
        eolica_pct = linha_ano.get("wind_share_elec", 0)
        hidro_pct = linha_ano.get("hydro_share_elec", 0)
        
        # 2. Arredonda cada valor individualmente para 1 casa decimal
        renovavel_val = round(renovavel_pct, 1) if pd.notna(renovavel_pct) else 0.0
        hidro_val = round(hidro_pct, 1) if pd.notna(hidro_pct) else 0.0
        eolica_val = round(eolica_pct, 1) if pd.notna(eolica_pct) else 0.0
        solar_val = round(solar_pct, 1) if pd.notna(solar_pct) else 0.0
        
        # 3. Calcula 'Outras Limpas' usando os valores já arredondados (evita a diferença de 0.1%)
        outras_renovaveis = max(0.0, round(renovavel_val - (hidro_val + eolica_val + solar_val), 1))

        # Layout com colunas proporcionais + coluna central com o sinal "="
        col_total, col_sinal, col_hidro, col_eolica, col_solar, col_outras = st.columns(
            [2.2, 0.4, 2, 2, 2, 2]
        )
        
        # 1. CARTÃO TOTAL
        with col_total:
            st.metric(
                "🌱 % Renovável Total", 
                f"{renovavel_val:.1f}%",
                help="Soma de todas as fontes limpas da matriz elétrica."
            )

        # 2. SINAL DE IGUAL (=)
        with col_sinal:
            st.markdown(
                """
                <div style="
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    height: 85px; 
                    font-size: 2rem; 
                    font-weight: 800; 
                    color: #10B981;">
                    =
                </div>
                """,
                unsafe_allow_html=True
            )

        # 3. DETALHAMENTO DAS FONTES QUE SOMAM O TOTAL
        with col_hidro:
            st.metric(
                "💧 Hidroelétrica", 
                f"{hidro_val:.1f}%",
                help="Participação da geração hídrica."
            )

        with col_eolica:
            st.metric(
                "💨 Eólica", 
                f"{eolica_val:.1f}%",
                help="Participação da geração eólica."
            )

        with col_solar:
            st.metric(
                "☀️ Solar", 
                f"{solar_val:.1f}%",
                help="Participação da geração solar."
            )

        with col_outras:
            st.metric(
                "🌴 Outras Limpas", 
                f"{outras_renovaveis:.1f}%",
                help="Biomassa, Geotérmica e outras renováveis menores."
            )
            
    else:
        st.warning("Sem dados para o ano selecionado.")

    st.markdown("---")
    
    col_graf1, col_graf2 = st.columns([1.2, 1])
    
    with col_graf1:
        st.markdown("#### Evolução da Participação Renovável (%)")
        fig_linha = px.line(
            df_pais,
            x="year",
            y="renewables_share_elec",
            title=f"Evolução da Matriz Limpa em {pais_selecionado}",
            labels={"year": "Ano", "renewables_share_elec": "% Renovável"},
            markers=True,
            color_discrete_sequence=[CORES["verde"]],
        )
        st.plotly_chart(estilizar_grafico(fig_linha), use_container_width=True)

    with col_graf2:
        st.markdown("#### Composição da Matriz Elétrica")
        if not df_ano.empty and pd.notna(renovavel_pct):
            df_pie = pd.DataFrame({
                "Fonte": ["Renovável (Solar/Eólica/Hidro)", "Fóssil / Outros"],
                "Valor": [renovavel_pct, max(0, 100 - renovavel_pct)]
            })
            fig_pie = px.pie(
                df_pie,
                names="Fonte",
                values="Valor",
                hole=0.6,
                color="Fonte",
                color_discrete_map={
                    "Renovável (Solar/Eólica/Hidro)": CORES["verde"],
                    "Fóssil / Outros": CORES["vermelho"]
                }
            )
            st.plotly_chart(estilizar_grafico(fig_pie), use_container_width=True)


# =========================================================
# PÁGINA 2: MATRIZ ELÉTRICA
# =========================================================
elif pagina == "Matriz Elétrica":
    st.markdown("### Detalhamento por Fonte de Energia")
    
    df_fontes = df_pais.melt(
        id_vars=["year"],
        value_vars=["solar_share_elec", "wind_share_elec", "hydro_share_elec", "fossil_share_elec"],
        var_name="Fonte",
        value_name="Percentual"
    )
    
    mapeamento_fontes = {
        "solar_share_elec": "Solar ☀️",
        "wind_share_elec": "Eólica 💨",
        "hydro_share_elec": "Hidrelétrica 💧",
        "fossil_share_elec": "Fóssil 🔥"
    }
    df_fontes["Fonte"] = df_fontes["Fonte"].map(mapeamento_fontes)
    
    fig_area = px.area(
        df_fontes,
        x="year",
        y="Percentual",
        color="Fonte",
        title=f"Evolução Temporal das Fontes em {pais_selecionado}",
        color_discrete_map={
            "Solar ☀️": CORES["amarelo"],
            "Eólica 💨": CORES["azul"],
            "Hidrelétrica 💧": CORES["verde"],
            "Fóssil 🔥": CORES["vermelho"]
        }
    )
    st.plotly_chart(estilizar_grafico(fig_area, 450), use_container_width=True)


# =========================================================
# PÁGINA 3: COMPARADOR GLOBAL
# =========================================================
elif pagina == "Comparador Global":
    st.markdown(f"### Ranking Global de Energia Renovável ({ano_selecionado})")
    
    df_ano_global = dados[(dados["year"] == ano_selecionado) & (dados["iso_code"].notna())].copy()
    top_paises = df_ano_global.sort_values("renewables_share_elec", ascending=False).head(15)
    
    fig_bar = px.bar(
        top_paises,
        x="renewables_share_elec",
        y="country",
        orientation="h",
        title=f"Top 15 Países com Maior Matriz Renovável em {ano_selecionado}",
        labels={"renewables_share_elec": "% Renovável", "country": "País"},
        color="renewables_share_elec",
        color_continuous_scale=["#1B6658", CORES["verde"]]
    )
    fig_bar.update_layout(yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False)
    st.plotly_chart(estilizar_grafico(fig_bar, 480), use_container_width=True)


# Rodapé
st.divider()
st.caption("Fonte: Our World in Data (Energy Dataset) · Atualização automática.")
