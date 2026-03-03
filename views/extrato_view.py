import streamlit as st
import pandas as pd
from datetime import datetime
from controllers import finance_controller

def render_extrato():
    st.title("📄 Extrato Detalhado")

    # FILTRO DE DATA
    col_mes, col_ano = st.columns([1, 1])
    meses_dict = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    hoje = datetime.now()
    with col_mes:
        sel_mes = st.selectbox("Mês", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=hoje.month-1, key="ext_mes")
    with col_ano:
        sel_ano = st.number_input("Ano", value=hoje.year, key="ext_ano")

    # CONTROLE DE EDIÇÃO
    if 'edit_trans_id' not in st.session_state: st.session_state['edit_trans_id'] = None

    # --- MODO EDIÇÃO ---
    if st.session_state['edit_trans_id']:
        st.info("✏️ Editando Transação...")
        t_edit = finance_controller.obter_transacao(st.session_state['edit_trans_id'])
        
        with st.container(border=True):
            try: d_val = pd.to_datetime(t_edit['data']).date()
            except: d_val = datetime.now().date()
            
            c1, c2 = st.columns(2)
            e_data = c1.date_input("Data", value=d_val)
            e_valor = c2.number_input("Valor", value=float(t_edit['valor']))
            
            c3, c4 = st.columns(2)
            e_cat = c3.selectbox("Categoria", ["Salário", "Extra", "Investimento", "Moradia", "Alimentação", "Transporte", "Lazer", "Contas", "Outros"], index=0)
            e_metodo = c4.selectbox("Pagamento", ["Pix", "Cartão", "Dinheiro", "Boleto", "Conta Fixa", "Transferência"], index=0)
            
            e_desc = st.text_input("Descrição", value=t_edit['descricao'])
            
            col_s, col_c = st.columns(2)
            if col_s.button("💾 Salvar Alterações"):
                finance_controller.atualizar_transacao(t_edit['id'], e_data, e_cat, e_valor, e_metodo, e_desc)
                st.session_state['edit_trans_id'] = None
                st.success("Transação atualizada!")
                st.rerun()
            if col_c.button("Cancelar"):
                st.session_state['edit_trans_id'] = None
                st.rerun()

    # --- MODO LISTAGEM ---
    else:
        df = finance_controller.obter_extrato(st.session_state['usuario_atual'], sel_mes, sel_ano)
        
        # Resumo do Topo
        receitas = df[df['tipo']=='Receita']['valor'].sum()
        despesas = df[df['tipo']=='Despesa']['valor'].sum()
        st.markdown(f"**Resumo de {meses_dict[sel_mes]}:** 🟢 Entradas: R$ {receitas:,.2f} | 🔴 Saídas: R$ {despesas:,.2f}")
        st.divider()

        if not df.empty:
            for idx, row in df.iterrows():
                # Estilo Visual (Card)
                with st.container(border=True):
                    c_data, c_info, c_val, c_btns = st.columns([1.5, 3, 2, 1.5])
                    
                    # Data
                    dt_str = row['data'].strftime('%d/%m')
                    c_data.markdown(f"📅 **{dt_str}**")
                    
                    # Info (Categoria e Descrição)
                    icon = "🟢" if row['tipo'] == 'Receita' else "🔴"
                    c_info.markdown(f"**{row['categoria']}**<br><span style='font-size:0.8em; color:gray'>{row['descricao']} ({row['metodo_pagamento']})</span>", unsafe_allow_html=True)
                    
                    # Valor
                    cor_val = "green" if row['tipo'] == 'Receita' else "red"
                    c_val.markdown(f":{cor_val}[**R$ {row['valor']:,.2f}**]")
                    
                    # Botões (usando columns dentro da column para alinhar)
                    b1, b2 = c_btns.columns(2)
                    if b1.button("✏️", key=f"ed_t_{row['id']}"):
                        st.session_state['edit_trans_id'] = row['id']
                        st.rerun()
                    if b2.button("🗑️", key=f"del_t_{row['id']}"):
                        finance_controller.excluir_transacao(row['id'])
                        st.rerun()
        else:
            st.info("Nenhuma movimentação neste período.")