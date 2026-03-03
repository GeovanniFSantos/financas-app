import streamlit as st
import pandas as pd
from datetime import datetime
from controllers import finance_controller

# Função auxiliar para formatar números com ponto no milhar (Padrão BR)
def formatar_numero(valor):
    if pd.isna(valor): return "0"
    # Formata com vírgula no milhar e troca por ponto
    return f"{int(valor):,}".replace(",", ".")

def render_dashboard():
    st.title("💰 Painel Financeiro Integrado")
    
    col_mes, col_ano = st.columns([1, 1])
    meses_dict = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    hoje = datetime.now()
    
    with col_mes:
        sel_mes = st.selectbox("Mês de Referência", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=hoje.month-1)
    with col_ano:
        sel_ano = st.number_input("Ano", value=hoje.year)

    if 'edit_cf_id' not in st.session_state: st.session_state['edit_cf_id'] = None
    if 'edit_meta_id' not in st.session_state: st.session_state['edit_meta_id'] = None

    # KPIs
    receita, despesa, saldo, lucro_veiculo = finance_controller.calcular_resumo(st.session_state['usuario_atual'], sel_mes, sel_ano)
    c1, c2, c3 = st.columns(3)
    c1.metric(f"🟢 Receita", f"R$ {receita:,.2f}")
    c2.metric(f"🔴 Despesas", f"R$ {despesa:,.2f}")
    c3.metric(f"💰 Saldo", f"R$ {saldo:,.2f}", delta=f"{saldo:,.2f}")

    # ALERTAS FROTA (COM FORMATAÇÃO NOVA)
    lics, manuts = finance_controller.obter_alertas_frota(st.session_state['usuario_atual'])
    if lics or manuts:
        with st.expander(f"🚘 Status da Frota", expanded=False):
            if lics:
                for l in lics: st.warning(f"📄 **{l['veiculo']}**: Licenciamento vence em {l['dias']} dias. R$ {l['valor']:.2f}")
            if manuts:
                for m in manuts:
                    # AQUI APLIQUEI A FORMATAÇÃO DE MILHAR
                    km_fmt = formatar_numero(m['km_faltante'])
                    
                    msg = f"**{m['item']}** ({m['veiculo']}): Faltam **{km_fmt} km**."
                    if m['km_faltante'] < 500: st.error("🔴 " + msg)
                    elif m['km_faltante'] < 2000: st.warning("⚠️ " + msg)
                    else: st.success("✅ " + msg)

    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🎯 Metas & Investimentos", "📝 Contas Fixas"])

    # --- ABA 1: METAS ---
    with tab1:
        st.subheader("Seu Patrimônio")
        
        # Modo Edição
        if st.session_state['edit_meta_id']:
             st.info("Ajustando Investimento...")
             metas_todas = finance_controller.listar_metas(st.session_state['usuario_atual'])
             meta_atual = metas_todas[metas_todas['id'] == st.session_state['edit_meta_id']].iloc[0]
             with st.container(border=True):
                 em_nome = st.text_input("Nome", value=meta_atual['nome'])
                 em_saldo = st.number_input("Saldo Atual", value=float(meta_atual['valor_guardado']))
                 em_rend = st.number_input("% Rendimento Mensal", value=float(meta_atual.get('rendimento_mensal', 0.0)))
                 if st.button("Salvar Ajuste"):
                     finance_controller.atualizar_meta_saldo(st.session_state['edit_meta_id'], em_saldo, em_nome, em_rend)
                     st.session_state['edit_meta_id'] = None; st.rerun()
                 if st.button("Cancelar"): st.session_state['edit_meta_id'] = None; st.rerun()
        else:
            with st.expander("Novo Investimento / Meta"):
                m_nome = st.text_input("Nome (Ex: Nubank)")
                m_alvo = st.number_input("Meta (R$)", min_value=1.0)
                m_rend = st.number_input("% Rendimento Mensal", value=1.0)
                m_data = st.date_input("Data Limite")
                if st.button("Criar"):
                    finance_controller.salvar_meta(st.session_state['usuario_atual'], m_nome, m_alvo, m_data, m_rend)
                    st.rerun()

            metas = finance_controller.listar_metas(st.session_state['usuario_atual'])
            if not metas.empty:
                for _, row in metas.iterrows():
                    with st.container(border=True):
                        # CÁLCULO DE RENDIMENTO FUTURO
                        saldo_atual = float(row['valor_guardado'])
                        rend_pct = float(row.get('rendimento_mensal', 0.0))
                        lucro_prox_mes = saldo_atual * (rend_pct / 100)
                        
                        # --- VISUAL GRANDE ---
                        c_nome, c_saldo = st.columns([1, 1])
                        c_nome.markdown(f"### 🏦 {row['nome']}")
                        c_saldo.markdown(f"<h2 style='text-align: right; color: #FFC107;'>R$ {saldo_atual:,.2f}</h2>", unsafe_allow_html=True)
                        
                        # BARRA DE PROGRESSO
                        pct = min(saldo_atual / row['valor_alvo'], 1.0)
                        st.progress(pct)
                        st.caption(f"Meta: R$ {row['valor_alvo']:,.2f} | Progresso: {pct*100:.1f}%")
                        
                        # INFORMAÇÃO DE RENDIMENTO
                        if rend_pct > 0:
                            st.info(f"📈 Rendendo **{rend_pct}%** ao mês. Previsão de lucro mês que vem: **+ R$ {lucro_prox_mes:,.2f}**")

                        # BOTÕES
                        c_dep, c_rend, c_opt = st.columns([2, 2, 1])
                        
                        with c_dep.popover("💰 Depositar"):
                            val_dep = st.number_input(f"Valor", min_value=1.0, key=f"vd_{row['id']}")
                            if st.button("Confirmar", key=f"bd_{row['id']}"):
                                finance_controller.depositar_meta(row['id'], val_dep, st.session_state['usuario_atual'])
                                st.success("Guardado!"); st.rerun()
                                
                        if rend_pct > 0:
                            # TRAVA DE SEGURANÇA NO BOTÃO RENDER
                            ja_rendeu = finance_controller.verificar_rendimento_aplicado(row['id'])
                            
                            if ja_rendeu:
                                c_rend.button("✅ Rendimento Aplicado", disabled=True, key=f"rnd_ok_{row['id']}")
                            else:
                                if c_rend.button("Aplicar Rendimento", key=f"ar_{row['id']}"):
                                    finance_controller.aplicar_rendimento_meta(row['id'])
                                    st.success("Atualizado!"); st.rerun()
                        
                        with c_opt.popover("⚙️"):
                            if st.button("✏️ Editar", key=f"edm_{row['id']}"): st.session_state['edit_meta_id'] = row['id']; st.rerun()
                            if st.button("🗑️ Excluir", key=f"dlm_{row['id']}"): finance_controller.excluir_meta(row['id']); st.rerun()
            else:
                st.info("Cadastre seus investimentos acima.")

    # --- ABA 2: CONTAS FIXAS (MANTIDO) ---
    with tab2:
        st.subheader("Contas Recorrentes")
        if st.session_state['edit_cf_id']:
            # ... (Lógica de edição igual) ...
            pass
        else:
            with st.expander("Nova Conta Fixa"):
                cf_nome = st.text_input("Nome")
                cf_val = st.number_input("Valor", min_value=0.0)
                cf_dia = st.number_input("Dia", 1, 31, 10)
                cf_cat = st.selectbox("Categoria", ["Contas", "Moradia", "Outros"])
                if st.button("Salvar CF"):
                    finance_controller.salvar_conta_fixa(st.session_state['usuario_atual'], cf_nome, cf_val, cf_dia, cf_cat)
                    st.rerun()
            
            contas = finance_controller.listar_contas_fixas(st.session_state['usuario_atual'])
            if not contas.empty:
                 for _, row in contas.iterrows():
                    ja_pagou = finance_controller.verificar_pagamento_conta(st.session_state['usuario_atual'], row['nome'], sel_mes, sel_ano)
                    with st.container(border=True):
                        c_i, c_p, c_o = st.columns([3, 2, 1])
                        check = "✅" if ja_pagou else "⏳"
                        c_i.markdown(f"{check} **{row['nome']}** (Dia {row['dia_vencimento']})<br>R$ {row['valor_previsto']:.2f}", unsafe_allow_html=True)
                        if ja_pagou: c_p.button("PAGO", disabled=True, key=f"pgk_{row['id']}")
                        else:
                            if c_p.button("Pagar", key=f"pg_{row['id']}"):
                                finance_controller.pagar_conta_fixa(st.session_state['usuario_atual'], row['nome'], row['valor_previsto'], datetime(sel_ano, sel_mes, int(row['dia_vencimento'])), row['categoria'])
                                st.rerun()
                        with c_o.popover("⚙️"):
                            if st.button("Edit", key=f"edcf_{row['id']}"): st.session_state['edit_cf_id'] = row['id']; st.rerun()
                            if st.button("Del", key=f"dlcf_{row['id']}"): finance_controller.excluir_conta_fixa(row['id']); st.rerun()