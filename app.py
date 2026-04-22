import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Meu Diário Wegovy", page_icon="💉", layout="wide")

# Nome do arquivo de dados
DB_FILE = "dados_wegovy.csv"

# Função para carregar ou criar o banco de dados
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    else:
        return pd.DataFrame(columns=["Data", "Dose (mg)", "Peso (kg)", "Local Aplicação", "Efeitos Colaterais", "Notas"])

df = load_data()

# --- SIDEBAR (Entrada de Dados) ---
st.sidebar.header("🆕 Novo Registro")
with st.sidebar.form("diario_form", clear_on_submit=True):
    data = st.date_input("Data", datetime.now())
    dose = st.selectbox("Dose Wegovy (mg)", [0.25, 0.5, 1.0, 1.7, 2.4])
    peso = st.number_input("Peso Atual (kg)", min_value=30.0, max_value=250.0, step=0.1)
    local = st.selectbox("Local da Injeção", ["Abdômen Esquerdo", "Abdômen Direito", "Coxa Esquerda", "Coxa Direita", "Braço Esquerdo", "Braço Direito"])
    sintomas = st.multiselect("Efeitos Colaterais", ["Nenhum", "Náusea", "Vômito", "Constipação", "Diarreia", "Cansaço", "Dor de Cabeça"])
    notas = st.text_area("Notas Adicionais")
    
    submit = st.form_submit_button("Salvar Registro")

if submit:
    new_data = pd.DataFrame({
        "Data": [pd.to_datetime(data)],
        "Dose (mg)": [dose],
        "Peso (kg)": [peso],
        "Local Aplicação": [local],
        "Efeitos Colaterais": [", ".join(sintomas)],
        "Notas": [notas]
    })
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    st.sidebar.success("Dados salvos com sucesso!")
    st.rerun()

# --- PAINEL PRINCIPAL ---
st.title("💉 Monitor de Evolução: Wegovy")

if not df.empty:
    # Métricas Rápidas
    col1, col2, col3 = st.columns(3)
    peso_inicial = df['Peso (kg)'].iloc[0]
    peso_atual = df['Peso (kg)'].iloc[-1]
    perda_total = peso_inicial - peso_atual
    
    col1.metric("Peso Atual", f"{peso_atual} kg")
    col2.metric("Perda Total", f"{perda_total:.1f} kg", delta=f"{-perda_total:.1f} kg", delta_color="normal")
    col3.metric("Última Dose", f"{df['Dose (mg)'].iloc[-1]} mg")

    # Gráfico de Evolução
    st.subheader("Gráfico de Perda de Peso")
    fig = px.line(df, x="Data", y="Peso (kg)", markers=True, title="Evolução do Peso")
    fig.update_layout(yaxis_title="Peso (kg)", xaxis_title="Data")
    st.plotly_chart(fig, use_container_width=True)

    # Histórico em Tabela
    st.subheader("Histórico de Aplicações")
    st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)

    # Botão para limpar dados (opcional)
    if st.checkbox("Mostrar opção para deletar histórico"):
        if st.button("Limpar todos os dados"):
            os.remove(DB_FILE)
            st.rerun()
else:
    st.info("Bem-vindo! Adicione seu primeiro registro na barra lateral para começar o acompanhamento.")

# Dicas de uso
with st.expander("ℹ️ Informações sobre o Wegovy"):
    st.write("""
    - **Escalonamento comum:** 0.25mg (4 semanas) -> 0.5mg (4 semanas) -> 1.0mg -> 1.7mg -> 2.4mg.
    - **Rodízio:** É importante alternar os locais de aplicação para evitar reações na pele.
    - **Hidratação:** Beba muita água para reduzir efeitos colaterais.
    """)