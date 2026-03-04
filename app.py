import streamlit as st
from views import login_view, dashboard_view, veiculos_view, diario_view, extrato_view, perfil_view # <--- IMPORTAR

st.set_page_config(page_title="Finanças App", layout="wide")


if 'logado' not in st.session_state: st.session_state['logado'] = False

def main():
    if not st.session_state['logado']:
        login_view.render_login()
    else:
        with st.sidebar:
            st.title(f"Olá, {st.session_state['nome_usuario']}")
            
            pagina = st.radio("Menu", [
                "📊 Financeiro", 
                "📄 Extrato",
                "📅 Diário de Bordo", 
                "🏍️ Veículos",
                "👤 Meu Perfil"  # <--- NOVA OPÇÃO
            ])
            
            st.markdown("---")
            st.sidebar.subheader("🚀 Conteúdo e Dicas")

            url_blog = "https://www.solucaosobmedida.com.br/blog/dashboards.html" 
            st.sidebar.markdown(
                f'''
                <a href="{url_blog}" target="_blank" style="text-decoration: none;">
                    <div style="
                        background-color: #007BFF; 
                        color: white; 
                        padding: 10px; 
                        border-radius: 8px; 
                        text-align: center; 
                        font-weight: bold; 
                        border: 1px solid #0056b3;">
                        🌐 Visitar Nosso Blog
                    </div>
                </a>
                ''', 
                unsafe_allow_html=True
            )
            st.sidebar.caption("Saiba mais sobre tecnologia e finanças.")
            if st.button("Sair", key="btn_sair_app"):
                st.session_state['logado'] = False
                st.rerun()
        
        if pagina == "📊 Financeiro":
            dashboard_view.render_dashboard()
        elif pagina == "📄 Extrato":
            extrato_view.render_extrato()
        elif pagina == "🏍️ Veículos":
            veiculos_view.render_veiculos()
        elif pagina == "📅 Diário de Bordo":
            diario_view.render_diario()
        elif pagina == "👤 Meu Perfil": # <--- ROTA
            perfil_view.render_perfil()

if __name__ == "__main__":
    main()