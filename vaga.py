import streamlit as st
import pandas as pd
import requests

# 1. Configuração da Página
st.set_page_config(page_title="Core Essence | Radar de Empregos", page_icon="💼", layout="wide")

# Estilização CSS para os Cards de Vagas
st.markdown("""
    <style>
    .vaga-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0275d8;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .vaga-titulo { color: #0275d8; font-size: 20px; font-weight: bold; }
    .fonte-tag { background-color: #e9ecef; padding: 2px 8px; border-radius: 5px; font-size: 12px; float: right; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO BUSCA ADZUNA ---
def buscar_adzuna(termo, local, qtd):
    try:
        url = "https://api.adzuna.com/v1/api/jobs/br/search/1"
        params = {
            "app_id": st.secrets["ADZUNA_ID"],
            "app_key": st.secrets["ADZUNA_KEY"],
            "results_per_page": qtd,
            "what": termo,
            "where": local,
            "content-type": "application/json"
        }
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return [{
                "titulo": v.get('title'),
                "empresa": v.get('company', {}).get('display_name', 'Confidencial'),
                "local": v.get('location', {}).get('display_name'),
                "desc": v.get('description', '')[:250] + "...",
                "url": v.get('redirect_url'),
                "fonte": "Adzuna"
            } for v in res.json().get('results', [])]
    except: return []
    return []

# --- FUNÇÃO BUSCA JOOBLE ---
def buscar_jooble(termo, local):
    try:
        url = f"https://br.jooble.org/api/{st.secrets['JOOBLE_KEY']}"
        payload = {"keywords": termo, "location": local}
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            return [{
                "titulo": v.get('title'),
                "empresa": v.get('company', 'Confidencial'),
                "local": v.get('location'),
                "desc": v.get('snippet', '').replace('<br/>', ' ')[:250] + "...",
                "url": v.get('link'),
                "fonte": "Jooble"
            } for v in res.json().get('jobs', [])]
    except: return []
    return []

# --- INTERFACE ---
def main():
    st.title("💼 Portal de Oportunidades Core Essence")
    st.markdown("Busca unificada em tempo real: **Adzuna + Jooble**")

    # Filtros
    with st.sidebar:
        st.header("🔍 Filtros")
        termo = st.text_input("O que você procura?", placeholder="Ex: Vendedor, Motorista...")
        local = st.text_input("Cidade ou Estado", placeholder="Ex: São Paulo")
        qtd = st.slider("Resultados por fonte", 5, 20, 10)
        btn = st.button("Buscar Agora")

    if btn:
        if not termo:
            st.error("Digite um cargo para buscar.")
            return

        with st.spinner('Consultando bases de dados...'):
            res_adzuna = buscar_adzuna(termo, local, qtd)
            res_jooble = buscar_jooble(termo, local)
            todas_vagas = res_adzuna + res_jooble

            if todas_vagas:
                st.success(f"Encontramos {len(todas_vagas)} vagas disponíveis!")
                for v in todas_vagas:
                    st.markdown(f"""
                    <div class="vaga-card">
                        <span class="fonte-tag">{v['fonte']}</span>
                        <div class="vaga-titulo">{v['titulo']}</div>
                        <p><b>🏢 {v['empresa']}</b> | 📍 {v['local']}</p>
                        <p style='font-size: 14px; color: #444;'>{v['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"🚀 Candidatar-se via {v['fonte']}", v['url'])
                    st.write("")
            else:
                st.warning("Nenhuma vaga encontrada para estes termos.")

if __name__ == "__main__":
    main()
