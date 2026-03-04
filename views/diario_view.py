import streamlit as st
from controllers import vehicle_controller, run_controller
from datetime import datetime
import pandas as pd

def render_diario():
    st.title("📅 Diário de Bordo")
    
    if 'editando_viagem_id' not in st.session_state: 
        st.session_state['editando_viagem_id'] = None

    veiculos = vehicle_controller.listar_veiculos(st.session_state['usuario_atual'])
    if veiculos.empty: return

    opts = veiculos.set_index('id')['nome'].to_dict()
    v_id = st.selectbox("Veículo", options=opts.keys(), format_func=lambda x: opts[x])

    # --- MODO EDIÇÃO ---
    if st.session_state['editando_viagem_id']:
        st.info("✏️ Editando Lançamento (Valores e KM serão recalculados)")
        run_edit = run_controller.obter_viagem(st.session_state['editando_viagem_id'])
        
        with st.container(border=True):
            # Converte string de data para objeto date
            try:
                data_obj = pd.to_datetime(run_edit['data']).date()
            except:
                data_obj = datetime.now()

            c1, c2 = st.columns(2)
            e_data = c1.date_input("Data", value=data_obj)
            e_km = c2.number_input("KM Rodados", value=float(run_edit['km_rodados']))
            
            c3, c4 = st.columns(2)
            e_fat = c3.number_input("Faturamento", value=float(run_edit['faturamento']))
            e_ent = c4.number_input("Entregas", value=float(run_edit['qtd_entregas']))
            
            e_extra = st.number_input("Gastos Extras", value=float(run_edit['gastos_extras']))
            e_desc = st.text_input("Desc.", value=str(run_edit.get('descricao_extra', ''))) # .get evita erro se coluna não existir
            
            col_s, col_c = st.columns(2)
            if col_s.button("💾 Salvar Correção"):
                ok, msg = run_controller.atualizar_diario(
                    run_edit['id'], e_data, e_km, e_fat, e_ent, e_extra, e_desc
                )
                if ok:
                    st.success(msg)
                    st.session_state['editando_viagem_id'] = None
                    st.rerun()
            
            if col_c.button("Cancelar"):
                st.session_state['editando_viagem_id'] = None
                st.rerun()

    else:
        with st.expander("📝 Novo Lançamento", expanded=False):
            # ... (Código de novo lançamento igual ao anterior) ...
            c1, c2 = st.columns(2)
            data = c1.date_input("Data", datetime.now())
            km = c2.number_input("KM Rodados", min_value=1, value=100)
            c3, c4 = st.columns(2)
            fat = c3.number_input("Faturamento", value=200.0)
            ent = c4.number_input("Entregas", value=0)
            ge = st.number_input("Gastos Extras", value=0.0)
            desc = st.text_input("Desc. Extra")
            
            if st.button("✅ Fechar Dia"):
                ok, msg = run_controller.salvar_diario(v_id, data, km, fat, ent, ge, desc)
                if ok: st.success(msg); st.rerun()

    # --- LISTAGEM ---
    st.divider()
    st.subheader("Histórico")
    df = run_controller.listar_viagens(v_id)
    if not df.empty:
        # Ordena por data (mais recente primeiro)
        df = df.sort_values(by='data', ascending=False)
        
        for idx, row in df.iterrows():
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 1, 1])
                data_str = pd.to_datetime(row['data']).strftime('%d/%m/%Y')
                
                col1.write(f"📅 **{data_str}**")
                col2.write(f"🛣️ {row['km_rodados']} km")
                col3.write(f"💰 Lucro: **R$ {row['lucro_liquido_calc']:.2f}**")
                
                # Botão Editar
                if col4.button("✏️", key=f"ed_run_{row['id']}"):
                    st.session_state['editando_viagem_id'] = row['id']
                    st.rerun()
                
                # Botão Excluir
                if col5.button("🗑️", key=f"del_run_{row['id']}"):
                    run_controller.excluir_viagem(row['id'])
                    st.rerun()