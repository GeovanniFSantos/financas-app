import streamlit as st
import pandas as pd
from datetime import datetime
from controllers import finance_controller

def render_extrato():
    st.title("📄 Extrato Detalhado")

    # --- 1. FORMULÁRIO DE NOVO LANÇAMENTO (VOLTAMOS COM ELE!) ---
    with st.expander("➕ Novo Lançamento Rápido (Receita / Despesa)", expanded=False):
        with st.form("form_novo_lancamento"):
            col_tipo, col_data = st.columns(2)
            tipo = col_tipo.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
            data = col_data.date_input("Data", datetime.now())

            col_cat, col_val = st.columns(2)
            # Categorias dinâmicas baseadas no tipo
            if tipo == "Receita":
                cats = ["Salário", "Extra", "Investimento", "Outros"]
            else:
                cats = ["Salário", "Moradia", "Alimentação", "Transporte", "Lazer", "Contas", "Metas/Investimento", "Outros"]
            
            categoria = col_cat.selectbox("Categoria", cats)
            valor = col_val.number_input("Valor R$", min_value=0.01, format="%.2f")

            col_met, col_desc = st.columns(2)
            metodo = col_met.selectbox("Pagamento", ["Pix", "Cartão", "Dinheiro", "Boleto", "Transferência"])
            descricao = col_desc.text_input("Descrição (Ex: Salário Mensal, Pizza)")

            submitted = st.form_submit_button("✅ Salvar Lançamento")
            
            if submitted:
                if valor > 0:
                    sucesso, msg = finance_controller.adicionar_transacao(
                        st.session_state['usuario_atual'], data, tipo, categoria, valor, metodo, descricao
                    )
                    if sucesso:
                        st.success("Lançado com sucesso!")
                        st.rerun() # Atualiza a página para aparecer na lista
                    else:
                        st.error(f"Erro: {msg}")
                else:
                    st.warning("O valor deve ser maior que zero.")

    st.divider()

    # --- 2. FILTROS DE VISUALIZAÇÃO ---
    col_mes, col_ano = st.columns([1, 1])
    meses_dict = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    hoje = datetime.now()
    
    with col_mes:
        sel_mes = st.selectbox("Mês", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=hoje.month-1, key="ext_mes")
    with col_ano:
        sel_ano = st.number_input("Ano", value=hoje.year, key="ext_ano")

    # CONTROLE DE EDIÇÃO
    if 'edit_trans_id' not in st.session_state: st.session_state['edit_trans_id'] = None

    # --- 3. MODO EDIÇÃO ---
    if st.session_state['edit_trans_id']:
        st.info("✏️ Editando Transação...")
        t_edit = finance_controller.obter_transacao(st.session_state['edit_trans_id'])
        
        with st.container(border=True):
            try: d_val = pd.to_datetime(t_edit['data']).date()
            except: d_val = datetime.now().date()
            
            c1, c2 = st.columns(2)
            e_data = c1.date_input("Data", value=d_val, key="ed_data")
            e_valor = c2.number_input("Valor", value=float(t_edit['valor']), key="ed_val")
            
            c3, c4 = st.columns(2)
            e_cat = c3.selectbox("Categoria", ["Salário", "Extra", "Investimento", "Moradia", "Alimentação", "Transporte", "Lazer", "Contas", "Outros"], index=0, key="ed_cat")
            e_metodo = c4.selectbox("Pagamento", ["Pix", "Cartão", "Dinheiro", "Boleto", "Conta Fixa", "Transferência"], index=0, key="ed_met")
            
            e_desc = st.text_input("Descrição", value=t_edit['descricao'], key="ed_desc")
            
            col_s, col_c = st.columns(2)
            if col_s.button("💾 Salvar Alterações"):
                finance_controller.atualizar_transacao(t_edit['id'], e_data, e_cat, e_valor, e_metodo, e_desc)
                st.session_state['edit_trans_id'] = None
                st.success("Transação atualizada!")
                st.rerun()
            if col_c.button("Cancelar"):
                st.session_state['edit_trans_id'] = None
                st.rerun()

    # --- 4. LISTAGEM (TABELA DE CARTÕES) ---
    else:
        df = finance_controller.obter_extrato(st.session_state['usuario_atual'], sel_mes, sel_ano)
        
        # Resumo do Topo
        receitas = df[df['tipo']=='Receita']['valor'].sum()
        despesas = df[df['tipo']=='Despesa']['valor'].sum()
        
        # Correção visual para saldo negativo/positivo
        saldo_mes = receitas - despesas
        cor_saldo = "green" if saldo_mes >= 0 else "red"
        
        st.markdown(f"**Resumo de {meses_dict[sel_mes]}:** 🟢 Entradas: R$ {receitas:,.2f} | 🔴 Saídas: R$ {despesas:,.2f} | Saldo: :{cor_saldo}[**R$ {saldo_mes:,.2f}**]")
        st.divider()

        if not df.empty:
            for idx, row in df.iterrows():
                # Estilo Visual (Card)
                with st.container(border=True):
                    c_data, c_info, c_val, c_btns = st.columns([1.5, 3, 2, 1.5])
                    
                    # Data
                    try:
                        dt_str = row['data'].strftime('%d/%m')
                    except:
                        dt_str = "Data Inv."

                    c_data.markdown(f"📅 **{dt_str}**")
                    
                    # Info (Categoria e Descrição)
                    c_info.markdown(f"**{row['categoria']}**<br><span style='font-size:0.8em; color:gray'>{row['descricao']} ({row['metodo_pagamento']})</span>", unsafe_allow_html=True)
                    
                    # Valor
                    cor_val = "green" if row['tipo'] == 'Receita' else "red"
                    sinal = "+" if row['tipo'] == 'Receita' else "-"
                    c_val.markdown(f":{cor_val}[**{sinal} R$ {row['valor']:,.2f}**]")
                    
                    # Botões
                    b1, b2 = c_btns.columns(2)
                    if b1.button("✏️", key=f"ed_t_{row['id']}"):
                        st.session_state['edit_trans_id'] = row['id']
                        st.rerun()
                    if b2.button("🗑️", key=f"del_t_{row['id']}"):
                        finance_controller.excluir_transacao(row['id'])
                        st.rerun()
        else:
            st.info("Nenhuma movimentação neste período.")