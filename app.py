import pandas as pd
import gspread
import plotly.express as px
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from datetime import date
from google.oauth2.service_account import Credentials

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
LOCATION_IMAGE_POINTS = {
    "Abdomen Esquerdo": (246, 315),
    "Abdomen Direito": (292, 315),
    "Abdomen": (270, 315),
    "Coxa Esquerda": (223, 468),
    "Coxa Direita": (317, 468),
    "Coxa": (270, 468),
    "Braco Esquerdo": (166, 255),
    "Braco Direito": (372, 255),
    "Braco": (270, 255),
}
BODY_IMAGE_PATH = "mapa corpo.webp"


def get_gspread_worksheet() -> gspread.Worksheet:
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    credentials_info = st.secrets["connections"]["gsheets"]["credentials"]

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(dict(credentials_info), scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_url(sheet_url).worksheet(WORKSHEET_NAME)


def load_data() -> pd.DataFrame:
    try:
        worksheet = get_gspread_worksheet()
        values = worksheet.get_all_values()
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

    if len(values) <= 1:
        return pd.DataFrame(columns=COLUMNS)

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[COLUMNS].copy()
    df["__sheet_row"] = range(2, 2 + len(df))
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Peso (kg)"] = pd.to_numeric(df["Peso (kg)"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    df["Dose (mg)"] = pd.to_numeric(df["Dose (mg)"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    return df


def append_row(new_row: dict) -> None:
    worksheet = get_gspread_worksheet()

    current_headers = worksheet.row_values(1)
    if not current_headers:
        worksheet.append_row(COLUMNS, value_input_option="USER_ENTERED")

    row_values = [
        pd.to_datetime(new_row["Data"]).strftime("%Y-%m-%d"),
        new_row["Dose (mg)"],
        new_row["Peso (kg)"],
        new_row["Local Aplicacao"],
        new_row["Efeitos Colaterais"],
        new_row["Notas"],
    ]
    worksheet.append_row(row_values, value_input_option="USER_ENTERED")


def delete_row(sheet_row: int) -> None:
    worksheet = get_gspread_worksheet()
    worksheet.delete_rows(sheet_row)


def get_latest_row_for_rotation(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None
    latest = df.dropna(subset=["Data", "Local Aplicacao"]).sort_values("Data")
    if latest.empty:
        return None
    return latest.iloc[-1]


def build_body_map_image(last_doses: pd.DataFrame) -> Image.Image:
    base_image = Image.open(BODY_IMAGE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(base_image)
    font = ImageFont.load_default()

    marker_colors = {
        "Ultima dose": (34, 197, 94, 255),
        "Penultima dose": (245, 158, 11, 255),
    }

    for _, row in last_doses.iterrows():
        local = str(row["Local Aplicacao"])
        if local not in LOCATION_IMAGE_POINTS:
            continue

        x, y = LOCATION_IMAGE_POINTS[local]
        label = "1" if row["Ordem"] == "Ultima dose" else "2"
        fill_color = marker_colors.get(row["Ordem"], (59, 130, 246, 255))

        radius = 18
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill_color, outline=(255, 255, 255, 255), width=3)

        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((x - text_w / 2, y - text_h / 2 - 1), label, fill=(255, 255, 255, 255), font=font)

    return base_image


def get_last_two_doses(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Data", "Local Aplicacao", "Ordem"])

    doses = (
        df.dropna(subset=["Data", "Local Aplicacao"])
        .sort_values("Data", ascending=False)
        .head(2)
        .copy()
    )
    if doses.empty:
        return pd.DataFrame(columns=["Data", "Local Aplicacao", "Ordem"])

    doses["Ordem"] = ["Ultima dose", "Penultima dose"][: len(doses)]
    return doses


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

st.subheader("Rodizio de Aplicacao (ultimas 2 doses)")
last_two_doses = get_last_two_doses(df)
st.image(build_body_map_image(last_two_doses), use_container_width=True)
if last_two_doses.empty:
    st.caption("Sem aplicacoes registradas ainda.")
else:
    latest_text = "-"
    previous_text = "-"
    latest_row = last_two_doses[last_two_doses["Ordem"] == "Ultima dose"]
    if not latest_row.empty:
        latest_item = latest_row.iloc[0]
        latest_text = f"{latest_item['Local Aplicacao']} em {latest_item['Data'].strftime('%d/%m/%Y')}"

    previous_row = last_two_doses[last_two_doses["Ordem"] == "Penultima dose"]
    if not previous_row.empty:
        previous_item = previous_row.iloc[0]
        previous_text = f"{previous_item['Local Aplicacao']} em {previous_item['Data'].strftime('%d/%m/%Y')}"

    info_col_1, info_col_2 = st.columns(2)
    info_col_1.metric("Ultima aplicacao", latest_text)
    info_col_2.metric("Penultima aplicacao", previous_text)
    st.caption("Marcador 1 = ultima dose | Marcador 2 = penultima dose")

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
    table_df = table_df.drop(columns=["__sheet_row"], errors="ignore")
    table_df["Data"] = table_df["Data"].dt.strftime("%Y-%m-%d")
    st.dataframe(table_df, use_container_width=True)

    st.subheader("Excluir Registro")
    delete_df = df.sort_values("Data", ascending=False).copy()
    if not delete_df.empty:
        delete_df = delete_df.reset_index(drop=True)
        delete_df["_label"] = delete_df.apply(
            lambda row: (
                f"{row['Data'].strftime('%Y-%m-%d') if pd.notna(row['Data']) else 'Sem data'}"
                f" | {row['Local Aplicacao']}"
                f" | {f'{row['Peso (kg)']:.1f} kg' if pd.notna(row['Peso (kg)']) else 'peso n/d'}"
                f" | {f'dose {row['Dose (mg)']:.2f} mg' if pd.notna(row['Dose (mg)']) else 'dose n/d'}"
            ),
            axis=1,
        )

        selected_label = st.selectbox(
            "Selecione o registro para excluir",
            options=delete_df["_label"].tolist(),
        )
        confirm_delete = st.checkbox("Confirmo que desejo excluir o registro selecionado")

        if st.button("Excluir registro", type="secondary", disabled=not confirm_delete):
            selected_row = delete_df[delete_df["_label"] == selected_label].iloc[0]
            sheet_row = int(selected_row["__sheet_row"])
            delete_row(sheet_row)
            st.success("Registro excluido com sucesso.")
            st.rerun()
else:
    st.info("Sem registros ainda. Adicione o primeiro registro na barra lateral.")