import streamlit as st
import pandas as pd
from datetime import datetime, date
from controllers import vehicle_controller

def render_veiculos():
    # --- INICIALIZAÇÃO DE ESTADO (Para os botões de editar funcionarem) ---
    if 'editando_veiculo_id' not in st.session_state: st.session_state['editando_veiculo_id'] = None
    if 'editando_manut_id' not in st.session_state: st.session_state['editando_manut_id'] = None

    st.title("🏍️ Gestão de Frota")

    tab_veic, tab_manut = st.tabs(["🚙 Meus Veículos", "🔧 Manutenções"])

    # ==========================================
    # ABA 1: VEÍCULOS
    # ==========================================
    with tab_veic:
        # --- MODO EDIÇÃO VEÍCULO ---
        if st.session_state['editando_veiculo_id']:
            st.info("✏️ Editando Veículo...")
            v_edit = vehicle_controller.obter_veiculo(st.session_state['editando_veiculo_id'])
            
            if v_edit is not None:
                with st.container(border=True):
                    ev_nome = st.text_input("Nome/Modelo", value=v_edit['nome'])
                    c1, c2 = st.columns(2)
                    ev_tipo = c1.selectbox("Tipo", ["Moto", "Carro", "Caminhão"], index=0 if v_edit['tipo'] == "Moto" else 1)
                    ev_placa = c2.text_input("Placa", value=v_edit['placa'])
                    
                    c3, c4 = st.columns(2)
                    # Tratamento de data para não quebrar
                    data_lic_bd = pd.to_datetime(v_edit['data_licenciamento']).date() if pd.notnull(v_edit['data_licenciamento']) else None
                    ev_data_lic = c3.date_input("Licenciamento", value=data_lic_bd)
                    ev_val_lic = c4.number_input("Valor Licenciamento", value=float(v_edit['valor_licenciamento']))
                    
                    c5, c6, c7 = st.columns(3)
                    ev_km = c5.number_input("KM Atual", value=float(v_edit['km_atual']))
                    ev_media = c6.number_input("Média Km/L", value=float(v_edit['media_consumo']))
                    ev_litro = c7.number_input("Preço Litro", value=float(v_edit['valor_litro_combustivel']))
                    
                    col_save, col_cancel = st.columns(2)
                    if col_save.button("💾 Salvar Alterações Veículo"):
                        vehicle_controller.atualizar_veiculo(
                            st.session_state['editando_veiculo_id'], 
                            ev_nome, ev_tipo, ev_placa, ev_data_lic, ev_val_lic, ev_km, ev_media, ev_litro
                        )
                        st.success("Veículo atualizado!")
                        st.session_state['editando_veiculo_id'] = None
                        st.rerun()
                        
                    if col_cancel.button("Cancelar"):
                        st.session_state['editando_veiculo_id'] = None
                        st.rerun()
            else:
                st.error("Erro ao carregar veículo.")
                st.session_state['editando_veiculo_id'] = None
                st.rerun()

        # --- MODO NOVO / LISTAGEM ---
        else:
            with st.expander("Novo Veículo"):
                with st.form("form_veiculo"):
                    nome = st.text_input("Nome/Modelo (Ex: Fan 160)")
                    c1, c2 = st.columns(2)
                    tipo = c1.selectbox("Tipo", ["Moto", "Carro", "Caminhão"])
                    placa = c2.text_input("Placa")
                    
                    c3, c4 = st.columns(2)
                    data_lic = c3.date_input("Data Licenciamento")
                    valor_lic = c4.number_input("Valor Licenciamento", min_value=0.0)
                    
                    c5, c6, c7 = st.columns(3)
                    km_atual = c5.number_input("KM Atual", min_value=0.0)
                    media = c6.number_input("Média Km/L", min_value=0.1, value=30.0)
                    preco_gas = c7.number_input("Preço Combustível", min_value=0.0, value=5.00)
                    
                    if st.form_submit_button("Salvar Veículo"):
                        vehicle_controller.salvar_veiculo(st.session_state['usuario_atual'], nome, tipo, placa, data_lic, valor_lic, km_atual, media, preco_gas)
                        st.success("Veículo cadastrado!")
                        st.rerun()

            # LISTAGEM
            veiculos = vehicle_controller.listar_veiculos(st.session_state['usuario_atual'])
            if not veiculos.empty:
                for _, row in veiculos.iterrows():
                    with st.container(border=True):
                        c_info, c_km, c_opt = st.columns([3, 2, 1])
                        c_info.markdown(f"**{row['nome']}** ({row['placa']})")
                        c_info.caption(f"Licenciamento: {vehicle_controller.formatar_data_mes_ano(row['data_licenciamento'])}")
                        
                        c_km.metric("KM", f"{float(row['km_atual']):,.0f} km")
                        
                        with c_opt.popover("⚙️"):
                            if st.button("Editar", key=f"edv_{row['id']}"):
                                st.session_state['editando_veiculo_id'] = row['id']
                                st.rerun()
                            if st.button("Excluir", key=f"delv_{row['id']}"):
                                vehicle_controller.excluir_veiculo(row['id'])
                                st.rerun()
            else:
                st.info("Nenhum veículo cadastrado.")

    # ==========================================
    # ABA 2: MANUTENÇÕES
    # ==========================================
    with tab_manut:
        veiculos_df = vehicle_controller.listar_veiculos(st.session_state['usuario_atual'])
        
        if veiculos_df.empty:
            st.warning("Cadastre um veículo primeiro.")
        else:
            # Seleção do Veículo
            opcoes_v = veiculos_df.set_index('id')['nome'].to_dict()
            sel_v_id = st.selectbox("Selecione o Veículo", list(opcoes_v.keys()), format_func=lambda x: opcoes_v[x])
            
            st.markdown("---")

            # --- MODO EDIÇÃO MANUTENÇÃO ---
            if st.session_state['editando_manut_id']:
                st.info("🔧 Editando Manutenção...")
                # Busca os dados atuais no banco
                m_edit = vehicle_controller.obter_manutencao(st.session_state['editando_manut_id'])
                
                if m_edit is not None:
                    with st.container(border=True):
                        em_item = st.text_input("Item (ex: Óleo)", value=m_edit['item'])
                        c1, c2 = st.columns(2)
                        em_km_int = c1.number_input("Trocar a cada (km)", value=float(m_edit['km_intervalo']))
                        em_custo = c2.number_input("Custo Estimado (R$)", value=float(m_edit['custo_estimado']))
                        
                        c3, c4 = st.columns(2)
                        em_km_ult = c3.number_input("KM Última Troca", value=float(m_edit['km_ultima_troca']))
                        
                        data_tr_bd = pd.to_datetime(m_edit['data_ultima_troca']).date() if pd.notnull(m_edit['data_ultima_troca']) else None
                        em_data_ult = c4.date_input("Data Última Troca", value=data_tr_bd)

                        col_save_m, col_cancel_m = st.columns(2)
                        
                        if col_save_m.button("💾 Salvar Alterações Manutenção"):
                            vehicle_controller.atualizar_manutencao(
                                st.session_state['editando_manut_id'],
                                em_item, em_km_int, em_custo, em_km_ult, em_data_ult
                            )
                            st.success("Manutenção atualizada!")
                            st.session_state['editando_manut_id'] = None
                            st.rerun()
                            
                        if col_cancel_m.button("Cancelar Edição"):
                            st.session_state['editando_manut_id'] = None
                            st.rerun()
                else:
                    st.error("Erro ao carregar manutenção.")
                    st.session_state['editando_manut_id'] = None
                    st.rerun()

            # --- MODO NOVO / LISTAGEM ---
            else:
                with st.expander("Nova Manutenção Preventiva"):
                    with st.form("form_manut", clear_on_submit=True):
                        item = st.text_input("Item (Ex: Troca de Óleo)")
                        c1, c2 = st.columns(2)
                        km_intervalo = c1.number_input("Trocar a cada (km)", min_value=100)
                        custo_est = c2.number_input("Custo Estimado (R$)", min_value=0.0)
                        
                        c3, c4 = st.columns(2)
                        km_ultima = c3.number_input("KM na Última Troca", min_value=0.0)
                        data_ultima = c4.date_input("Data da Última Troca")
                        
                        if st.form_submit_button("Cadastrar Manutenção"):
                            vehicle_controller.salvar_manutencao(sel_v_id, item, km_intervalo, custo_est, km_ultima, data_ultima)
                            st.success("Cadastrado!")
                            st.rerun()

                # TABELA DE MANUTENÇÕES
                manuts = vehicle_controller.listar_manutencoes(sel_v_id)
                
                # Busca KM atual do veículo para calcular progresso
                v_atual = veiculos_df[veiculos_df['id'] == sel_v_id].iloc[0]
                km_moto = float(v_atual['km_atual'])

                if not manuts.empty:
                    for _, m in manuts.iterrows():
                        km_prox = float(m['km_ultima_troca']) + float(m['km_intervalo'])
                        km_restante = km_prox - km_moto
                        progresso = max(0.0, min(1.0, 1 - (km_restante / float(m['km_intervalo']))))
                        
                        cor = "green"
                        if km_restante < 500: cor = "red"
                        elif km_restante < 1000: cor = "orange"

                        with st.container(border=True):
                            c_tit, c_prog = st.columns([1, 2])
                            c_tit.markdown(f"**{m['item']}**")
                            c_tit.caption(f"R$ {float(m['custo_estimado']):.2f}")
                            
                            c_prog.progress(progresso)
                            c_prog.markdown(f":{cor}[Faltam **{km_restante:.0f} km**]")
                            
                            # Botões de Ação
                            c_b1, c_b2, c_b3 = st.columns([2, 1, 1])
                            
                            # Registrar Troca Rápida
                            with c_b1.popover("✅ Registrar Troca"):
                                n_km = st.number_input("Novo KM", value=km_moto, key=f"nk_{m['id']}")
                                n_dt = st.date_input("Data", key=f"nd_{m['id']}")
                                if st.button("Confirmar", key=f"conf_{m['id']}"):
                                    vehicle_controller.registrar_troca_manutencao(m['id'], n_km, n_dt)
                                    st.success("Atualizado!")
                                    st.rerun()
                            
                            # Editar
                            if c_b2.button("✏️", key=f"edm_{m['id']}"):
                                st.session_state['editando_manut_id'] = m['id']
                                st.rerun()
                                
                            # Excluir
                            if c_b3.button("🗑️", key=f"delm_{m['id']}"):
                                vehicle_controller.excluir_manutencao(m['id'])
                                st.rerun()
                else:
                    st.info("Nenhuma manutenção cadastrada para este veículo.")