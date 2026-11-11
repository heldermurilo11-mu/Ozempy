# Ozempy — Monitor de Evolução GLP-1 / Wegovy

Aplicação web em **Streamlit** para acompanhamento pessoal de aplicações de GLP-1 (**Wegovy**), controle de peso, registro de efeitos colaterais e rodízio anatômico de locais de injeção com persistência em **Google Sheets**.

---

## Principais Funcionalidades

- **Mapa Corporal Interativo de Rodízio (`mapa corpo.webp`)**: plota com Pillow os marcadores das duas últimas aplicações (`1 = última dose`, `2 = penúltima dose`) e calcula automaticamente a janela recomendada de 14 dias para evitar repetição do mesmo ponto anatômico.
- **Lançamento na Barra Lateral**: registro de data, dose (`0.25`, `0.5`, `1.0`, `1.7`, `2.4 mg`), peso atual (`kg`), local da injeção, efeitos colaterais e observações.
- **Indicadores e Evolução do Peso**: métricas de peso atual, perda acumulada e última dose, além de gráfico interativo de linha com **Plotly**.
- **Histórico e Exclusão Segura**: tabela completa ordenada por data e exclusão de registros diretamente na planilha com confirmação explícita.
- **Persistência em Nuvem**: leitura, inclusão e remoção de linhas via `gspread` autenticado por **Service Account** do Google Cloud.

---

## Pré-requisitos

- **Python 3.12+**
- Planilha no **Google Sheets** com uma aba (ex.: `Registros`) e permissões de edição concedidas ao e-mail da **Service Account** do Google Cloud (`client_email`) com acesso às APIs **Google Sheets API** e **Google Drive API**.

---

## Configuração Local

### 1. Ambiente Virtual e Dependências

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Credenciais e Planilha (`secrets.toml`)

Copie o modelo de segredos e preencha com os dados da sua planilha e Service Account:

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edite `.streamlit/secrets.toml` configurando:
- `spreadsheet`: URL completa da sua planilha do Google Sheets.
- `worksheet`: nome da aba utilizada na planilha (padrão: `"Registros"`).
- `[connections.gsheets.credentials]`: campos do JSON da chave privada da sua Service Account.

> **Importante:** `.streamlit/secrets.toml` e arquivos `*.json` estão listados no `.gitignore` e nunca devem ser versionados.

### 3. Executar a Aplicação

```powershell
streamlit run app.py
```

---

## Estrutura do Projeto

```text
.
├── app.py                            # Aplicação Streamlit, integração gspread e mapa corporal
├── mapa corpo.webp                   # Imagem base usada para os marcadores de rodízio
├── requirements.txt                  # Dependências Python
├── .streamlit/
│   └── secrets.toml.example          # Modelo seguro de configuração e Service Account
└── README.md
```
