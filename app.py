import streamlit as st
from views import login_view, dashboard_view, veiculos_view, diario_view, extrato_view, perfil_view, admin_view 

st.set_page_config(page_title="Solução Sob Medida - App Finançeiro", layout="wide")

if 'logado' not in st.session_state: 
    st.session_state['logado'] = False

def main():
    if not st.session_state['logado']:
        login_view.render_login()
    else:
        with st.sidebar:
            st.title(f"🛠️ Gestão: {st.session_state['nome_usuario']}")
            
            # --- LÓGICA DE SEPARAÇÃO DE MENUS ---
            if st.session_state.get('nivel_acesso') == 'admin':
                # Visão exclusiva do DONO (Você)
                opcoes_menu = ["🛡️ Painel ADM", "👤 Meu Perfil"]
            else:
                # Visão exclusiva do CLIENTE (Quem paga)
                opcoes_menu = [
                    "📊 Financeiro", 
                    "📄 Extrato",
                    "📅 Diário de Bordo", 
                    "🏍️ Veículos",
                    "👤 Meu Perfil"
                ]

            pagina = st.radio("Navegação", opcoes_menu)
            
            st.markdown("---")
            # O Blog continua para ambos (bom para suporte e marketing)
            url_blog = "https://www.solucaosobmedida.com.br/blog/dashboards.html" 
            st.sidebar.markdown(f'<a href="{url_blog}" target="_blank">🌐 Visitar Blog</a>', unsafe_allow_html=True)
            
            if st.button("Sair", key="btn_sair_app"):
                st.session_state['logado'] = False
                st.rerun()
        
        # --- ROTEAMENTO DINÂMICO ---
        if pagina == "🛡️ Painel ADM":
            admin_view.exibir_painel_adm()
        elif pagina == "👤 Meu Perfil":
            perfil_view.render_perfil()
        elif pagina == "📊 Financeiro":
            dashboard_view.render_dashboard()
        elif pagina == "📄 Extrato":
            extrato_view.render_extrato()
        elif pagina == "🏍️ Veículos":
            veiculos_view.render_veiculos()
        elif pagina == "📅 Diário de Bordo":
            diario_view.render_diario()

if __name__ == "__main__":
    main()