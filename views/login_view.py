import streamlit as st
import time
from controllers import finance_controller

def render_login():
    if 'menu_atual' not in st.session_state:
        st.session_state['menu_atual'] = 'login'

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acesso")
        
        # --- TELA DE LOGIN ---
        if st.session_state['menu_atual'] == 'login':
            with st.container(border=True):
                st.subheader("Entrar")
                user = st.text_input("Usuário ou E-mail")
                password = st.text_input("Senha", type="password")
                
                if st.button("Entrar"):
                    nome = finance_controller.realizar_login(user, password)
                    if nome:
                        st.session_state['logado'] = True
                        st.session_state['usuario_atual'] = user.strip().lower()
                        st.session_state['nome_usuario'] = nome
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
                
                st.markdown("---")
                if st.button("Criar Conta"):
                    st.session_state['menu_atual'] = 'cadastro'
                    st.rerun()

        # --- TELA DE CADASTRO ---
        elif st.session_state['menu_atual'] == 'cadastro':
            with st.container(border=True):
                st.subheader("Novo Cadastro")
                new_user = st.text_input("Usuário")
                new_name = st.text_input("Nome Completo")
                new_email = st.text_input("E-mail")
                new_contact = st.text_input("WhatsApp")
                new_pass = st.text_input("Senha", type="password")
                
                if st.button("Cadastrar"):
                    if new_user and new_name and new_pass:
                        sucesso, msg = finance_controller.cadastrar_usuario(
                            new_user, new_name, new_email, new_contact, new_pass
                        )
                        if sucesso:
                            st.success(msg)
                            time.sleep(1)
                            st.session_state['menu_atual'] = 'login'
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Preencha tudo!")
                
                st.markdown("---")
                if st.button("Voltar"):
                    st.session_state['menu_atual'] = 'login'
                    st.rerun()