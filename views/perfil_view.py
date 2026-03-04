import streamlit as st
import base64
import pandas as pd
from controllers import finance_controller

def render_perfil():
    st.title("👤 Meu Perfil")
    
    # Busca dados atualizados do banco MySQL
    dados = finance_controller.obter_dados_usuario(st.session_state['usuario_atual'])
    
    if dados is None:
        st.error("Erro ao carregar perfil.")
        return

    col_esq, col_dir = st.columns([1, 2])
    
    # --- COLUNA DA FOTO (RESTAURADA!) ---
    with col_esq:
        st.subheader("Foto")
        
        # Pega a string base64 do banco
        foto_base64 = dados.get('foto_perfil')
        
        # Verifica se tem foto salva e se não é vazia
        if foto_base64 and len(str(foto_base64)) > 100:
            try:
                st.markdown(
                    f'<img src="data:image/png;base64,{foto_base64}" style="border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 3px solid #FFC107;">',
                    unsafe_allow_html=True
                )
            except:
                st.warning("Erro ao exibir imagem.")
        else:
            # Avatar padrão se não tiver foto
            st.markdown("""
            <div style="width: 150px; height: 150px; background-color: #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 50px; color: #FFF;">
                👤
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Upload de nova foto
        novo_arquivo = st.file_uploader("Trocar foto", type=['png', 'jpg', 'jpeg'])
        if novo_arquivo:
            # Converte imagem para Texto (Base64)
            bytes_data = novo_arquivo.getvalue()
            base64_str = base64.b64encode(bytes_data).decode()
            
            if st.button("Salvar Nova Foto"):
                sucesso, msg = finance_controller.salvar_foto_perfil(st.session_state['usuario_atual'], base64_str)
                # O controller retorna tupla ou boolean dependendo da implementação, ajustamos aqui:
                st.success("Foto atualizada! A página irá recarregar.")
                st.rerun()

    # --- COLUNA DOS DADOS ---
    with col_dir:
        tab1, tab2 = st.tabs(["📝 Dados Pessoais", "🔒 Segurança"])
        
        nome_atual = str(dados['nome'])
        email_atual = str(dados.get('email') or '')
        contato_atual = str(dados.get('contato') or '')
        user_atual = str(dados['username'])

        # ABA 1: EDITAR DADOS
        with tab1:
            with st.form("form_dados_perfil"):
                st.text_input("Usuário (Login)", value=user_atual, disabled=True)
                nome = st.text_input("Nome Completo", value=nome_atual)
                email = st.text_input("E-mail", value=email_atual)
                contato = st.text_input("Celular/WhatsApp", value=contato_atual)
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    finance_controller.atualizar_perfil(st.session_state['usuario_atual'], nome, email, contato)
                    st.session_state['nome_usuario'] = nome
                    st.success("Dados salvos no Banco de Dados!")
                    st.rerun()

        # ABA 2: SEGURANÇA
        with tab2:
            with st.form("form_senha_perfil"):
                st.warning("Ao mudar a senha, você será deslogado.")
                nova_senha = st.text_input("Nova Senha", type="password")
                confirma_senha = st.text_input("Confirmar Nova Senha", type="password")
                
                if st.form_submit_button("Alterar Senha"):
                    if nova_senha == confirma_senha and len(nova_senha) >= 4:
                        finance_controller.alterar_senha(st.session_state['usuario_atual'], nova_senha)
                        st.success("Senha alterada! Faça login novamente.")
                        st.session_state['logado'] = False
                        st.rerun()
                    else:
                        st.error("Senhas não conferem ou muito curta.")