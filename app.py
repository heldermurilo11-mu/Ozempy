import pandas as pd
import plotly.express as px
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


df = load_data()

st.sidebar.header("Novo Registro")
with st.sidebar.form("wegovy_form", clear_on_submit=True):
    data = st.date_input("Data", value=date.today())
    dose = st.selectbox("Dose Wegovy (mg)", [0.25, 0.5, 1.0, 1.7, 2.4])
    peso = st.number_input("Peso Atual (kg)", min_value=30.0, max_value=350.0, step=0.1)
    local = st.selectbox("Local de Aplicacao", ["Coxa", "Abdomen", "Braco", "Outro"])
    efeitos = st.multiselect(
        "Efeitos Colaterais",
        ["Nenhum", "Nausea", "Vomito", "Constipacao", "Diarreia", "Cansaco", "Dor de cabeca"],
    )
    notas = st.text_area("Notas")

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

    st.subheader("Historico Completo")
    table_df = df.sort_values("Data", ascending=False).copy()
    table_df["Data"] = table_df["Data"].dt.strftime("%Y-%m-%d")
    st.dataframe(table_df, use_container_width=True)
else:
    st.info("Sem registros ainda. Adicione o primeiro registro na barra lateral.")