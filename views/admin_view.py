import streamlit as st
from controllers import admin_controller
from datetime import date, timedelta

def exibir_painel_adm():
    st.title("🛡️ Gestão de Assinaturas")
    
    # 1. PRIMEIRO: Busca os usuários (importante ser a primeira coisa!)
    usuarios = admin_controller.listar_todos_usuarios()
    
    # 2. SEGUNDO: Faz as contas e exibe o resumo
    if not usuarios.empty:
        qtd_ativos = len(usuarios[usuarios['status_conta'] == 'ativo'])
        st.info(f"📈 Você possui {qtd_ativos} clientes ativos no momento.")
        
        # 3. TERCEIRO: Renderiza a lista de gerenciamento
        for index, row in usuarios.iterrows():
            # Formata a data para exibição (trata se for None)
            data_exp = row['data_expiracao'] if row['data_expiracao'] else "Sem validade"
            
            with st.expander(f"👤 {row['username']} - Expira em: {data_exp}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nova_data = st.date_input(
                        "Nova Validade", 
                        value=row['data_expiracao'] if row['data_expiracao'] else date.today() + timedelta(days=30),
                        key=f"date_{row['id']}"
                    )
                    if st.button("Atualizar Validade", key=f"btn_date_{row['id']}"):
                        admin_controller.definir_validade(row['id'], nova_data)
                        st.success("Data atualizada!")
                        st.rerun()
                
                with col2:
                    status_atual = row['status_conta']
                    label = "🚫 Suspender Acesso" if status_atual == "ativo" else "✅ Reativar Acesso"
                    novo_status = "suspenso" if status_atual == "ativo" else "ativo"
                    
                    if st.button(label, key=f"btn_stat_{row['id']}"):
                        admin_controller.alterar_status_usuario(row['id'], novo_status)
                        st.rerun()
    else:
        st.warning("Nenhum cliente encontrado para gerenciar.")