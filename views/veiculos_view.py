import streamlit as st
import pandas as pd
from datetime import datetime
from controllers import vehicle_controller

def render_veiculos():
    st.title("🏍️ Gestão de Frota")
    
    if 'editando_veiculo_id' not in st.session_state: st.session_state['editando_veiculo_id'] = None
    if 'editando_manut_id' not in st.session_state: st.session_state['editando_manut_id'] = None

    tab1, tab2 = st.tabs(["Meu Veículo", "🔧 Manutenção"])
    
    # --- ABA 1: VEÍCULOS ---
    with tab1:
        if st.session_state['editando_veiculo_id']:
            st.info("✏️ Editando Veículo...")
            v_edit = vehicle_controller.obter_veiculo(st.session_state['editando_veiculo_id'])
            
            with st.container(border=True):
                c_a, c_b, c_c = st.columns(3)
                e_nome = c_a.text_input("Modelo", value=v_edit['nome'])
                e_tipo = c_b.selectbox("Tipo", ["Moto", "Carro"], index=0 if v_edit['tipo']=="Moto" else 1)
                e_placa = c_c.text_input("Placa", value=v_edit.get('placa', ''))

                c_d, c_e = st.columns(2)
                
                # --- CORREÇÃO DO ERRO NaT ---
                # Verifica se a data é nula (NaT) ou inválida
                data_banco = pd.to_datetime(v_edit.get('data_licenciamento'))
                if pd.isna(data_banco):
                    d_lic_val = datetime.now().date()
                else:
                    d_lic_val = data_banco.date()
                # ----------------------------

                e_data_lic = c_d.date_input("Vencimento Licenciamento", value=d_lic_val)
                e_val_lic = c_e.number_input("Valor IPVA/Licenc.", value=float(v_edit.get('valor_licenciamento', 0.0)))
                
                st.markdown("---")
                c1, c2, c3 = st.columns(3)
                e_km = c1.number_input("KM Atual", value=float(v_edit['km_atual']))
                e_media = c2.number_input("Km/L", value=float(v_edit['media_consumo']))
                e_litro = c3.number_input("R$ Gasolina", value=float(v_edit['valor_litro_combustivel']))
                
                col_save, col_cancel = st.columns(2)
                if col_save.button("💾 Salvar Alterações"):
                    vehicle_controller.atualizar_veiculo(v_edit['id'], e_nome, e_tipo, e_placa, e_data_lic, e_val_lic, e_km, e_media, e_litro)
                    st.session_state['editando_veiculo_id'] = None
                    st.success("Atualizado!")
                    st.rerun()
                if col_cancel.button("Cancelar"):
                    st.session_state['editando_veiculo_id'] = None
                    st.rerun()

        else:
            with st.expander("Cadastrar Novo Veículo"):
                c_a, c_b, c_c = st.columns(3)
                nome = c_a.text_input("Modelo")
                tipo = c_b.selectbox("Tipo", ["Moto", "Carro"])
                placa = c_c.text_input("Placa")
                
                c_d, c_e = st.columns(2)
                data_lic = c_d.date_input("Vencimento Licenciamento", datetime.now())
                val_lic = c_e.number_input("Valor IPVA/Licenc.", value=200.0)

                st.markdown("---")
                c1, c2, c3 = st.columns(3)
                km = c1.number_input("KM Atual", min_value=0)
                media = c2.number_input("Km/L", value=30.0)
                litro = c3.number_input("R$ Gasolina", value=6.19)
                
                if st.button("Salvar Veículo"):
                    vehicle_controller.salvar_veiculo(st.session_state['usuario_atual'], nome, tipo, placa, data_lic, val_lic, km, media, litro)
                    st.rerun()

        st.divider()
        veiculos = vehicle_controller.listar_veiculos(st.session_state['usuario_atual'])
        if not veiculos.empty:
            for index, row in veiculos.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([4, 1, 1])
                    placa_txt = f"[{row.get('placa', 'SEM PLACA')}]"
                    c1.write(f"**{row['nome']}** {placa_txt} | KM: {row['km_atual']}")
                    if c2.button("✏️", key=f"edv_{row['id']}"):
                        st.session_state['editando_veiculo_id'] = row['id']; st.rerun()
                    if c3.button("🗑️", key=f"dlv_{row['id']}"):
                        vehicle_controller.excluir_veiculo(row['id']); st.rerun()

    # --- ABA 2: MANUTENÇÃO ---
    with tab2:
        st.subheader("Peças e Trocas")
        veiculos = vehicle_controller.listar_veiculos(st.session_state['usuario_atual'])
        if not veiculos.empty:
            opts = veiculos.set_index('id')['nome'].to_dict()
            v_id = st.selectbox("Selecione Veículo", options=opts.keys(), format_func=lambda x: opts[x])
            
            if st.session_state['editando_manut_id']:
                st.warning("🔧 Editando Peça...")
                m_edit = vehicle_controller.obter_manutencao(st.session_state['editando_manut_id'])
                with st.container(border=True):
                    em_item = st.text_input("Peça", value=m_edit['item'])
                    c1, c2 = st.columns(2)
                    em_custo = c1.number_input("Custo R$", value=float(m_edit['custo_estimado']))
                    em_interv = c2.number_input("Durabilidade (Km)", value=float(m_edit['km_intervalo']))
                    
                    c3, c4 = st.columns(2)
                    em_ult_km = c3.number_input("Km Última Troca", value=float(m_edit['km_ultima_troca']))
                    
                    # --- CORREÇÃO DO ERRO NaT (MANUTENÇÃO) ---
                    data_manut = pd.to_datetime(m_edit.get('data_ultima_troca'))
                    if pd.isna(data_manut):
                        d_ult_val = datetime.now().date()
                    else:
                        d_ult_val = data_manut.date()
                    # -----------------------------------------
                    
                    em_ult_data = c4.date_input("Data da Troca", value=d_ult_val)
                    
                    if st.button("💾 Atualizar"):
                        vehicle_controller.atualizar_manutencao(m_edit['id'], em_item, em_interv, em_custo, em_ult_km, em_ult_data)
                        st.session_state['editando_manut_id'] = None; st.rerun()
                    if st.button("Cancelar"): st.session_state['editando_manut_id'] = None; st.rerun()
            else:
                with st.expander("Adicionar Nova Regra"):
                    c1, c2 = st.columns(2)
                    item = c1.text_input("Peça")
                    custo = c2.number_input("Custo R$", value=100.0)
                    c3, c4 = st.columns(2)
                    interv = c3.number_input("Durabilidade (Km)", value=10000)
                    
                    st.write("Dados da Última Troca:")
                    cc1, cc2 = st.columns(2)
                    ult_km = cc1.number_input("KM no Painel", value=0)
                    ult_data = cc2.date_input("Data Realizada", datetime.now())
                    
                    if st.button("Salvar Regra"):
                        vehicle_controller.salvar_manutencao(v_id, item, interv, custo, ult_km, ult_data)
                        st.rerun()

                st.write("Regras Ativas:")
                manuts = vehicle_controller.listar_manutencoes(v_id)
                if not manuts.empty:
                    for idx, m in manuts.iterrows():
                        c1, c2, c3 = st.columns([4, 1, 1])
                        # Formata data para exibir
                        data_fmt = vehicle_controller.formatar_data_mes_ano(m.get('data_ultima_troca'))
                        c1.write(f"🔧 **{m['item']}** (Trocou em: {data_fmt})")
                        if c2.button("✏️", key=f"edm_{m['id']}"): st.session_state['editando_manut_id'] = m['id']; st.rerun()
                        if c3.button("🗑️", key=f"dlm_{m['id']}"): vehicle_controller.excluir_manutencao(m['id']); st.rerun()