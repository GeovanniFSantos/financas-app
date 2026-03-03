import streamlit as st
# IMPORTAR O NOVO EXTRATO_VIEW
from views import login_view, dashboard_view, veiculos_view, diario_view, extrato_view 

st.set_page_config(page_title="Finanças App", layout="wide")
st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 8px; height: 3em; background-color: #FFC107; color: black; border: none; font-weight: bold;}
    .stButton>button:hover {background-color: #ffca2c; color: black;}
    h1 {text-align: center;}
</style>
""", unsafe_allow_html=True)

if 'logado' not in st.session_state: st.session_state['logado'] = False

def main():
    if not st.session_state['logado']:
        login_view.render_login()
    else:
        with st.sidebar:
            st.title(f"Olá, {st.session_state['nome_usuario']}")
            
            # NOVO MENU
            pagina = st.radio("Menu", [
                "📊 Financeiro", 
                "📄 Extrato",         # <--- NOVO
                "📅 Diário de Bordo", 
                "🏍️ Veículos"
            ])
            
            st.markdown("---")
            if st.button("Sair", key="btn_sair_app"):
                st.session_state['logado'] = False
                st.rerun()
        
        # ROTEAMENTO
        if pagina == "📊 Financeiro":
            dashboard_view.render_dashboard()
        elif pagina == "📄 Extrato":      # <--- ROTA NOVA
            extrato_view.render_extrato()
        elif pagina == "🏍️ Veículos":
            veiculos_view.render_veiculos()
        elif pagina == "📅 Diário de Bordo":
            diario_view.render_diario()

if __name__ == "__main__":
    main()