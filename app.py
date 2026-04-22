import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Meu Diario Wegovy", page_icon="💉", layout="wide")

COLUMNS = [
    "Data",
    "Dose (mg)",
    "Peso (kg)",
    "Local Aplicacao",
    "Efeitos Colaterais",
    "Notas",
]
WORKSHEET_NAME = "Murilo"
LOCATION_OPTIONS = [
    "Abdomen Esquerdo",
    "Abdomen Direito",
    "Coxa Esquerda",
    "Coxa Direita",
    "Braco Esquerdo",
    "Braco Direito",
    "Outro",
]
LOCATION_POINTS = {
    "Abdomen Esquerdo": (-0.35, 0.2),
    "Abdomen Direito": (0.35, 0.2),
    "Coxa Esquerda": (-0.28, -0.72),
    "Coxa Direita": (0.28, -0.72),
    "Braco Esquerdo": (-0.95, 0.2),
    "Braco Direito": (0.95, 0.2),
    "Abdomen": (0.0, 0.2),
    "Coxa": (0.0, -0.72),
    "Braco": (0.0, 0.2),
}


def get_connection() -> GSheetsConnection:
    return st.connection("gsheets", type=GSheetsConnection)


def load_data() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = conn.read(worksheet=WORKSHEET_NAME, ttl=0)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

    if df is None or df.empty:
        return pd.DataFrame(columns=COLUMNS)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[COLUMNS].copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Peso (kg)"] = pd.to_numeric(df["Peso (kg)"], errors="coerce")
    df["Dose (mg)"] = pd.to_numeric(df["Dose (mg)"], errors="coerce")
    return df


def append_row(new_row: dict) -> None:
    conn = get_connection()
    current_df = load_data()
    updated_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
    conn.update(worksheet=WORKSHEET_NAME, data=updated_df)


def get_latest_row_for_rotation(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None
    latest = df.dropna(subset=["Data", "Local Aplicacao"]).sort_values("Data")
    if latest.empty:
        return None
    return latest.iloc[-1]


def build_body_map(last_doses: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    # Silhueta simples para referencia visual.
    body_line = dict(color="#E2E8F0", width=2.5)
    body_fill = "rgba(148, 163, 184, 0.16)"
    head_fill = "rgba(148, 163, 184, 0.22)"
    fig.add_shape(type="circle", x0=-0.18, x1=0.18, y0=0.92, y1=1.25, line=body_line, fillcolor=head_fill)
    fig.add_shape(type="rect", x0=-0.35, x1=0.35, y0=-0.12, y1=0.92, line=body_line, fillcolor=body_fill)
    fig.add_shape(type="rect", x0=-1.05, x1=-0.35, y0=0.12, y1=0.52, line=body_line, fillcolor=body_fill)
    fig.add_shape(type="rect", x0=0.35, x1=1.05, y0=0.12, y1=0.52, line=body_line, fillcolor=body_fill)
    fig.add_shape(type="rect", x0=-0.35, x1=-0.02, y0=-1.25, y1=-0.12, line=body_line, fillcolor=body_fill)
    fig.add_shape(type="rect", x0=0.02, x1=0.35, y0=-1.25, y1=-0.12, line=body_line, fillcolor=body_fill)

    labels = []
    xs = []
    ys = []
    colors = []
    sizes = []

    for _, row in last_doses.iterrows():
        local = str(row["Local Aplicacao"])
        if local not in LOCATION_POINTS:
            continue
        x, y = LOCATION_POINTS[local]
        xs.append(x)
        ys.append(y)
        dose_label = row["Ordem"]
        labels.append(f"{dose_label}: {local} ({row['Data'].strftime('%d/%m/%Y')})")
        if dose_label == "Ultima dose":
            colors.append("#22C55E")
            sizes.append(20)
        else:
            colors.append("#F59E0B")
            sizes.append(16)

    if xs:
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                text=["2" if c == "#F59E0B" else "1" for c in colors],
                textposition="middle center",
                marker=dict(size=sizes, color=colors, line=dict(color="white", width=2)),
                hovertext=labels,
                hoverinfo="text",
                showlegend=False,
            )
        )

    fig.update_layout(
        title="Mapa Corporal - Ultimas 2 Doses",
        xaxis=dict(visible=False, range=[-1.25, 1.25]),
        yaxis=dict(visible=False, range=[-1.35, 1.35], scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#0F172A",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        title_font=dict(color="#F8FAFC"),
    )
    return fig


df = load_data()

latest_row = get_latest_row_for_rotation(df)
rotation_help = "Troque o ponto de aplicacao a cada dose."
if latest_row is not None:
    days_since_last = (pd.to_datetime(date.today()) - latest_row["Data"]).days
    last_loc = str(latest_row["Local Aplicacao"])
    if pd.notna(latest_row["Data"]) and days_since_last < 14:
        remaining = 14 - days_since_last
        rotation_help = (
            f"Ultima dose em {last_loc} ha {days_since_last} dia(s). "
            f"Evite o mesmo ponto por mais {remaining} dia(s) e mantenha pelo menos 1 cm de distancia."
        )

st.sidebar.header("Novo Registro")
with st.sidebar.form("wegovy_form", clear_on_submit=True):
    data = st.date_input("Data", value=date.today())
    dose = st.selectbox("Dose Wegovy (mg)", [0.25, 0.5, 1.0, 1.7, 2.4])
    peso = st.number_input("Peso Atual (kg)", min_value=30.0, max_value=350.0, step=0.1)
    local = st.selectbox("Local da Injecao", LOCATION_OPTIONS)
    efeitos = st.multiselect(
        "Efeitos Colaterais",
        ["Nenhum", "Nausea", "Vomito", "Constipacao", "Diarreia", "Cansaco", "Dor de cabeca"],
    )
    notas = st.text_area("Notas")
    st.caption(rotation_help)

    submit = st.form_submit_button("Salvar")

if submit:
    payload = {
        "Data": pd.to_datetime(data),
        "Dose (mg)": dose,
        "Peso (kg)": peso,
        "Local Aplicacao": local,
        "Efeitos Colaterais": ", ".join(efeitos) if efeitos else "",
        "Notas": notas,
    }

    with st.spinner("Salvando no Google Sheets..."):
        append_row(payload)
    st.sidebar.success("Registro salvo com sucesso.")
    st.rerun()

st.title("Monitor de Evolucao: Wegovy")

if not df.empty:
    valid_df = df.dropna(subset=["Data", "Peso (kg)"]).sort_values("Data").copy()

    if not valid_df.empty:
        peso_inicial = valid_df["Peso (kg)"].iloc[0]
        peso_atual = valid_df["Peso (kg)"].iloc[-1]
        perda_total = peso_inicial - peso_atual
        ultima_dose = valid_df["Dose (mg)"].iloc[-1]

        col1, col2, col3 = st.columns(3)
        col1.metric("Peso Atual", f"{peso_atual:.1f} kg")
        col2.metric("Perda Total", f"{perda_total:.1f} kg")
        col3.metric("Ultima Dose", f"{ultima_dose:.2f} mg")

        st.subheader("Evolucao do Peso")
        fig = px.line(valid_df, x="Data", y="Peso (kg)", markers=True, title="Evolucao do peso")
        fig.update_layout(xaxis_title="Data", yaxis_title="Peso (kg)")
        st.plotly_chart(fig, use_container_width=True)

    last_two_doses = (
        df.dropna(subset=["Data", "Local Aplicacao"]) 
        .sort_values("Data", ascending=False)
        .head(2)
        .copy()
    )
    if not last_two_doses.empty:
        last_two_doses["Ordem"] = ["Ultima dose", "Penultima dose"][: len(last_two_doses)]
        st.subheader("Rodizio de Aplicacao (ultimas 2 doses)")
        st.plotly_chart(build_body_map(last_two_doses), use_container_width=True)
        st.caption("Marcador 1 = ultima dose | Marcador 2 = penultima dose")

    st.subheader("Historico Completo")
    table_df = df.sort_values("Data", ascending=False).copy()
    table_df["Data"] = table_df["Data"].dt.strftime("%Y-%m-%d")
    st.dataframe(table_df, use_container_width=True)
else:
    st.info("Sem registros ainda. Adicione o primeiro registro na barra lateral.")