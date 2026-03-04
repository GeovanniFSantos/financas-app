import streamlit as st
import pandas as pd
from controllers import finance_controller

def render_perfil():
    st.title("👤 Meu Perfil")
    
    # Busca dados atualizados do banco
    dados = finance_controller.obter_dados_usuario(st.session_state['usuario_atual'])
    
    if dados is None:
        st.error("Erro ao carregar perfil.")
        return

    # --- COLUNA ÚNICA DOS DADOS (REMOVI A FOTO) ---
    tab1, tab2 = st.tabs(["📝 Dados Pessoais", "🔒 Segurança"])
    
    # Tratamento de erro para garantir que NaN vira texto vazio ""
    nome_atual = str(dados['nome']) if not pd.isna(dados['nome']) else ""
    email_atual = str(dados.get('email', '')) if not pd.isna(dados.get('email')) else ""
    contato_atual = str(dados.get('contato', '')) if not pd.isna(dados.get('contato')) else ""
    user_atual = str(dados['username']) if not pd.isna(dados['username']) else ""

    # ABA 1: EDITAR DADOS PESSOAIS
    with tab1:
        st.subheader("Atualizar Informações de Contato")
        with st.form("form_dados_perfil"):
            # Username não pode mudar (é a chave do banco), então fica desabilitado
            st.text_input("Usuário (Login)", value=user_atual, disabled=True, help="O nome de usuário não pode ser alterado.")
            
            nome = st.text_input("Nome Completo", value=nome_atual)
            email = st.text_input("E-mail", value=email_atual)
            contato = st.text_input("Celular/WhatsApp", value=contato_atual)
            
            submitted = st.form_submit_button("💾 Salvar Alterações Pessoais")
            
            if submitted:
                if nome:
                    finance_controller.atualizar_perfil(st.session_state['usuario_atual'], nome, email, contato)
                    st.session_state['nome_usuario'] = nome # Atualiza o nome no menu lateral instantaneamente
                    st.success("Dados pessoais atualizados com sucesso!")
                    st.rerun()
                else:
                    st.error("O campo Nome é obrigatório.")

    # ABA 2: SEGURANÇA (ALTERAR SENHA)
    with tab2:
        st.subheader("Alterar Senha de Acesso")
        with st.form("form_senha_perfil"):
            st.warning("⚠️ Ao alterar sua senha, você será deslogado para confirmar a nova credencial.")
            
            nova_senha = st.text_input("Nova Senha", type="password")
            confirma_senha = st.text_input("Confirmar Nova Senha", type="password")
            
            submitted_senha = st.form_submit_button("🔒 Alterar Senha Definitivemente")
            
            if submitted_senha:
                # Validações básicas de senha
                if not nova_senha:
                    st.error("A nova senha não pode estar vazia.")
                elif nova_senha != confirma_senha:
                    st.error("As senhas digitadas não coincidem. Tente novamente.")
                elif len(nova_senha) < 4:
                    st.warning("Para sua segurança, use uma senha com pelo menos 4 caracteres.")
                else:
                    # Salva o Hash da nova senha
                    sucesso, msg = finance_controller.alterar_senha(st.session_state['usuario_atual'], nova_senha)
                    if sucesso:
                        st.success("Senha alterada com sucesso! Deslogando...")
                        # Desloga o usuário para ele logar com a senha nova
                        st.session_state['logado'] = False
                        st.rerun()
                    else:
                        st.error(f"Erro ao alterar senha: {msg}")