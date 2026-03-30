import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração da Página
st.set_page_config(page_title="Core Essence | Radar de Empregos", page_icon="💼", layout="wide")

# --- FUNÇÃO PARA SALVAR LOG DE PESQUISA ---
def salvar_log_pesquisa(termo, local, qtd_encontrada):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        sh = client.open_by_key(st.secrets["ID_LICENCAS"])
        wks = sh.worksheet("LOG_PESQUISAS")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        wks.append_row([agora, termo, local, qtd_encontrada])
    except Exception as e:
        st.sidebar.error(f"Erro no Google Sheets: {e}")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .vaga-card {
        background-color: #ffffff; padding: 20px; border-radius: 10px;
        border-left: 5px solid #0275d8; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .vaga-titulo { color: #0275d8; font-size: 20px; font-weight: bold; }
    .fonte-tag { background-color: #e9ecef; padding: 2px 8px; border-radius: 5px; font-size: 12px; float: right; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BUSCA COM DEBUG ---
def buscar_adzuna(termo, local, qtd):
    try:
        # Puxa dos secrets e limpa QUALQUER caractere não alfanumérico (espaços, traços, tabs)
        import re
        raw_id = str(st.secrets["ADZUNA_ID"])
        raw_key = str(st.secrets["ADZUNA_KEY"])
        
        # O re.sub remove tudo que não for letra ou número
        app_id = re.sub(r'[^a-zA-Z0-9]', '', raw_id)
        app_key = re.sub(r'[^a-zA-Z0-9]', '', raw_key)

        url = "https://api.adzuna.com/v1/api/jobs/br/search/1"
        params = {
            "app_id": app_id, 
            "app_key": app_key,
            "results_per_page": qtd, 
            "what": termo, 
            "where": local, 
            "content-type": "application/json"
        }
        
        # Usamos uma sessão para manter a conexão estável
        session = requests.Session()
        res = session.get(url, params=params, timeout=10)
        
        st.sidebar.write(f"📡 Adzuna Status: {res.status_code}")
        
        if res.status_code == 200:
            vagas = res.json().get('results', [])
            return [{
                "titulo": v.get('title'), 
                "empresa": v.get('company', {}).get('display_name', 'Confidencial'),
                "local": v.get('location', {}).get('display_name'), 
                "desc": v.get('description', '')[:250] + "...",
                "url": v.get('redirect_url'), 
                "fonte": "Adzuna"
            } for v in vagas]
        else:
            # Se falhar, vamos tentar imprimir o erro bruto para você ver no Log
            st.sidebar.warning(f"Adzuna diz: {res.text}")
            return []
    except Exception as e:
        st.sidebar.error(f"Erro na requisição: {e}")
        return []
def buscar_jooble(termo, local):
    try:
        url = f"https://br.jooble.org/api/{st.secrets['JOOBLE_KEY']}"
        payload = {"keywords": termo, "location": local}
        res = requests.post(url, json=payload)
        
        st.sidebar.write(f"📡 Jooble Status: {res.status_code}")
        
        if res.status_code == 200:
            return [{
                "titulo": v.get('title'), "empresa": v.get('company', 'Confidencial'),
                "local": v.get('location'), "desc": v.get('snippet', '').replace('<br/>', ' ')[:250] + "...",
                "url": v.get('link'), "fonte": "Jooble"
            } for v in res.json().get('jobs', [])]
        else:
            st.sidebar.error(f"Erro Jooble: {res.text}")
            return []
    except Exception as e:
        st.sidebar.error(f"Falha de conexão Jooble: {e}")
        return []

# --- INTERFACE PRINCIPAL ---
def main():
    st.title("💼 Portal de Oportunidades Core Essence")
    
    with st.sidebar:
        st.header("🔍 Filtros de Busca")
        termo = st.text_input("O que você procura?", placeholder="Ex: Vendedor, TI...")
        local = st.text_input("Cidade ou Estado", placeholder="Ex: Brasil")
        qtd = st.slider("Resultados por fonte", 5, 20, 10)
        btn = st.button("Buscar Agora")

    if btn:
        if not termo:
            st.error("Por favor, digite um cargo.")
            return

        # Ajuste de localidade padrão
        local_final = local if local else "Brasil"

        with st.spinner(f'Buscando "{termo}" em "{local_final}"...'):
            res_adzuna = buscar_adzuna(termo, local_final, qtd)
            res_jooble = buscar_jooble(termo, local_final)
            todas_vagas = res_adzuna + res_jooble

            salvar_log_pesquisa(termo, local_final, len(todas_vagas))

            if todas_vagas:
                st.success(f"Encontramos {len(todas_vagas)} vagas disponíveis!")
                for v in todas_vagas:
                    with st.container():
                        st.markdown(f"""
                        <div class="vaga-card">
                            <span class="fonte-tag">{v['fonte']}</span>
                            <div class="vaga-titulo">{v['titulo']}</div>
                            <p><b>🏢 {v['empresa']}</b> | 📍 {v['local']}</p>
                            <p style='font-size: 14px; color: #444;'>{v['desc']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.link_button(f"🚀 Candidatar-se via {v['fonte']}", v['url'])
                        st.write("---")
            else:
                st.warning(f"Nenhuma vaga de '{termo}' encontrada em '{local_final}'. Tente um termo mais genérico.")

if __name__ == "__main__":
    main()
