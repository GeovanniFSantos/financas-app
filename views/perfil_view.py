import streamlit as st
import base64
import pandas as pd
from datetime import datetime, date
from controllers import finance_controller

def render_perfil():
    st.title("👤 Meu Perfil")
    
    dados = finance_controller.obter_dados_usuario(st.session_state['usuario_atual'])
    
    if dados is None:
        st.error("Erro ao carregar perfil.")
        return

    col_esq, col_dir = st.columns([1, 2])
    
    # --- FOTO ---
    with col_esq:
        foto_base64 = dados.get('foto_perfil')
        if foto_base64 and len(str(foto_base64)) > 100:
            st.markdown(f'<img src="data:image/png;base64,{foto_base64}" style="border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 3px solid #FFC107;">', unsafe_allow_html=True)
        else:
            st.markdown('<div style="width: 150px; height: 150px; background-color: #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 50px;">👤</div>', unsafe_allow_html=True)
            
        novo_arquivo = st.file_uploader("Trocar foto", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
        if novo_arquivo:
            bytes_data = novo_arquivo.getvalue()
            base64_str = base64.b64encode(bytes_data).decode()
            if st.button("Salvar Nova Foto"):
                finance_controller.salvar_foto_perfil(st.session_state['usuario_atual'], base64_str)
                st.success("Foto atualizada!")
                st.rerun()

    # --- DADOS ---
    with col_dir:
        tab1, tab2 = st.tabs(["📝 Dados Pessoais", "🔒 Segurança"])
        
        with tab1:
            with st.form("form_dados_perfil"):
                st.text_input("Usuário (Login)", value=str(dados['username']), disabled=True)
                nome = st.text_input("Nome Completo", value=str(dados['nome']))
                email = st.text_input("E-mail", value=str(dados.get('email') or ''))
                contato = st.text_input("Celular/WhatsApp", value=str(dados.get('contato') or ''))
                
                # --- CORREÇÃO DA DATA AQUI ---
                data_bd = dados.get('data_nascimento')
                
                # 1. Define limites
                min_data = date(1900, 1, 1)
                max_data = datetime.now().date()

                # 2. Define o valor padrão SEGURO
                if pd.notnull(data_bd) and str(data_bd).strip() != "":
                    try:
                        valor_data = pd.to_datetime(data_bd).date()
                    except:
                        valor_data = date(1990, 1, 1)
                else:
                    valor_data = date(1990, 1, 1)

                # 3. Garante que o valor está dentro dos limites para não dar erro
                if valor_data < min_data: valor_data = min_data
                if valor_data > max_data: valor_data = max_data

                nascimento = st.date_input(
                    "Data de Nascimento", 
                    value=valor_data, 
                    min_value=min_data, 
                    max_value=max_data, 
                    format="DD/MM/YYYY"
                )
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    finance_controller.atualizar_perfil(st.session_state['usuario_atual'], nome, email, contato, nascimento)
                    st.session_state['nome_usuario'] = nome
                    st.success("Perfil atualizado!")
                    st.rerun()

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