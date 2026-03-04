import streamlit as st
import pandas as pd
from datetime import datetime
from controllers import finance_controller
from views import graficos_view

def render_dashboard():
    # --- 1. INICIALIZAÇÃO DE VARIÁVEIS DE ESTADO (Para edição funcionar) ---
    if 'edit_meta_id' not in st.session_state: st.session_state['edit_meta_id'] = None
    if 'edit_cf_id' not in st.session_state: st.session_state['edit_cf_id'] = None

    st.title("💰 Painel Financeiro Integrado")
    
    # --- 2. FILTROS DE DATA ---
    col_mes, col_ano = st.columns(2)
    meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    hoje = datetime.now()
    
    with col_mes:
        nome_meses = list(meses.values())
        # Tenta pegar mês atual ou selecionado anteriormente
        mes_atual_idx = hoje.month - 1
        sel_mes_nome = st.selectbox("Mês de Referência", nome_meses, index=mes_atual_idx)
        sel_mes = list(meses.keys())[list(meses.values()).index(sel_mes_nome)]
        
    with col_ano:
        sel_ano = st.number_input("Ano", min_value=2020, max_value=2030, value=hoje.year)

    # --- 3. CÁLCULOS (NOVA LÓGICA QUE CRIAMOS HOJE) ---
    receita, despesa, saldo, lucro_veiculo = finance_controller.calcular_resumo(st.session_state['usuario_atual'], sel_mes, sel_ano)
    
    st.markdown("---")

    # --- 4. CARTÕES DE RESUMO (Topo) ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric(
            label="🟢 Faturamento Bruto (Receita)", 
            value=f"R$ {receita:,.2f}", 
            help="Soma de todo valor recebido nas viagens e receitas manuais, SEM descontos."
        )
        
    with c2:
        st.metric(
            label="🔴 Custos & Despesas", 
            value=f"R$ {despesa:,.2f}", 
            help="Inclui: Gasolina, Manutenção, Depreciação e Contas Pagas."
        )
        
    with c3:
        st.metric(
            label="💰 Lucro Líquido (Saldo)", 
            value=f"R$ {saldo:,.2f}", 
            delta=f"{saldo:,.2f}",
            help="O que sobrou no bolso (Receita - Despesas)."
        )

    # --- DETALHE DA FROTA ---
    st.markdown("---")

    st.markdown("### 📊 Análise de Gastos")
    col_graf1, col_graf2 = st.columns([1.5, 1]) # 1.5 para o gráfico, 1 para uma tabelinha de resumo

    with col_graf1:
        st.write("**Gastos por Categoria**")
        df_gastos = finance_controller.obter_dados_pizza(st.session_state['usuario_atual'], sel_mes, sel_ano)
        graficos_view.exibir_grafico_gastos(df_gastos)

    with col_graf2:
        st.write("**Resumo de Saídas**")
        if not df_gastos.empty:
            # Ordena do maior gasto para o menor
            df_resumo = df_gastos.sort_values(by='total', ascending=False)
            # Formata como moeda para a tabela
            df_resumo['total'] = df_resumo['total'].apply(lambda x: f"R$ {x:,.2f}")
            st.table(df_resumo.set_index('categoria'))
        else:
            st.caption("Nada para listar.")
    
    st.markdown("---")

    with st.expander("🚙 Detalhes da Frota (Custos e Lucros)", expanded=False):
        st.info(f"Deste saldo total, **R$ {lucro_veiculo:,.2f}** vieram do lucro líquido das entregas/viagens.")
        
        # Alertas de manutenção/licenciamento
        try:
            lics, manuts = finance_controller.obter_alertas_frota(st.session_state['usuario_atual'])
            if lics or manuts:
                st.markdown("---")
                if lics:
                    st.error(f"⚠️ Licenciamentos vencendo: {len(lics)}")
                    for l in lics: st.write(f"- {l['veiculo']}: R$ {l['valor']} (Vence em {l['dias']} dias)")
                if manuts:
                    st.warning(f"🔧 Manutenções Próximas: {len(manuts)}")
                    for m in manuts: st.write(f"- {m['veiculo']} ({m['item']}): Falta {m['km_faltante']:.0f} km")
        except: pass

    # --- 5. ABAS (AQUI ENTRA O SEU CÓDIGO COMPLETO) ---
    tab_meta, tab_contas = st.tabs(["🎯 Metas & Investimentos", "📄 Contas Fixas"])
    
    # === ABA 1: METAS ===
    with tab_meta:
        st.subheader("Seu Patrimônio")
        
        # Modo Edição
        if st.session_state['edit_meta_id']:
             st.info("Ajustando Investimento...")
             metas_todas = finance_controller.listar_metas(st.session_state['usuario_atual'])
             # Filtra para achar a meta que está sendo editada
             if not metas_todas.empty:
                 meta_atual = metas_todas[metas_todas['id'] == st.session_state['edit_meta_id']]
                 if not meta_atual.empty:
                     meta_atual = meta_atual.iloc[0]
                     with st.container(border=True):
                         em_nome = st.text_input("Nome", value=meta_atual['nome'])
                         em_saldo = st.number_input("Saldo Atual", value=float(meta_atual['valor_guardado']))
                         em_rend = st.number_input("% Rendimento Mensal", value=float(meta_atual.get('rendimento_mensal', 0.0)))
                         
                         col_save, col_cancel = st.columns(2)
                         if col_save.button("Salvar Ajuste"):
                             finance_controller.atualizar_meta_saldo(st.session_state['edit_meta_id'], em_saldo, em_nome, em_rend)
                             st.session_state['edit_meta_id'] = None
                             st.rerun()
                         if col_cancel.button("Cancelar"): 
                             st.session_state['edit_meta_id'] = None
                             st.rerun()
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
                    meta_valor = float(row['valor_alvo'])
                    pct = min(saldo_atual / meta_valor, 1.0) if meta_valor > 0 else 0
                    st.progress(pct)
                    st.caption(f"Meta: R$ {meta_valor:,.2f} | Progresso: {pct*100:.1f}%")
                    
                    # INFORMAÇÃO DE RENDIMENTO
                    if rend_pct > 0:
                        st.info(f"📈 Rendendo **{rend_pct}%** ao mês. Previsão de lucro mês que vem: **+ R$ {lucro_prox_mes:,.2f}**")

                    # BOTÕES
                    c_dep, c_rend, c_opt = st.columns([2, 2, 1])
                    
                    with c_dep.popover("💰 Depositar"):
                        val_dep = st.number_input(f"Valor", min_value=1.0, key=f"vd_{row['id']}")
                        if st.button("Confirmar", key=f"bd_{row['id']}"):
                            finance_controller.depositar_meta(row['id'], val_dep, st.session_state['usuario_atual'])
                            st.success("Guardado!")
                            st.rerun()
                            
                    if rend_pct > 0:
                        # TRAVA DE SEGURANÇA NO BOTÃO RENDER
                        ja_rendeu = finance_controller.verificar_rendimento_aplicado(row['id'])
                        
                        if ja_rendeu:
                            c_rend.button("✅ Rendimento Aplicado", disabled=True, key=f"rnd_ok_{row['id']}")
                        else:
                            if c_rend.button("Aplicar Rendimento", key=f"ar_{row['id']}"):
                                finance_controller.aplicar_rendimento_meta(row['id'])
                                st.success("Atualizado!")
                                st.rerun()
                    else:
                        c_rend.write("") # Espaço vazio se não tiver rendimento
                    
                    with c_opt.popover("⚙️"):
                        if st.button("✏️ Editar", key=f"edm_{row['id']}"): 
                            st.session_state['edit_meta_id'] = row['id']
                            st.rerun()
                        if st.button("🗑️ Excluir", key=f"dlm_{row['id']}"): 
                            finance_controller.excluir_meta(row['id'])
                            st.rerun()
        else:
            st.info("Nenhuma meta cadastrada.")

    # === ABA 2: CONTAS FIXAS ===
    with tab_contas:
        st.subheader("Contas Recorrentes")
        
        if st.session_state['edit_cf_id']:
            # Modo Edição Conta Fixa
            st.info("Editando Conta...")
            contas_todas = finance_controller.listar_contas_fixas(st.session_state['usuario_atual'])
            if not contas_todas.empty:
                conta_atual = contas_todas[contas_todas['id'] == st.session_state['edit_cf_id']]
                if not conta_atual.empty:
                    conta_atual = conta_atual.iloc[0]
                    with st.container(border=True):
                        ec_nome = st.text_input("Nome", value=conta_atual['nome'])
                        ec_val = st.number_input("Valor", value=float(conta_atual['valor_previsto']))
                        ec_dia = st.number_input("Dia Vencimento", value=int(conta_atual['dia_vencimento']), min_value=1, max_value=31)
                        ec_cat = st.selectbox("Categoria", ["Casa", "Serviços", "Pessoal", "Cartão de Crédito", "Emprestimo", "Outros"], index=0) # Simplificado index
                        
                        col_cs, col_cc = st.columns(2)
                        if col_cs.button("Salvar Conta"):
                            finance_controller.atualizar_conta_fixa(st.session_state['edit_cf_id'], ec_nome, ec_val, ec_dia, ec_cat)
                            st.session_state['edit_cf_id'] = None
                            st.rerun()
                        if col_cc.button("Cancelar Edição"):
                            st.session_state['edit_cf_id'] = None
                            st.rerun()
        else:
            with st.expander("Nova Conta Fixa"):
                cf_nome = st.text_input("Nome")
                cf_val = st.number_input("Valor Previsto", min_value=0.0)
                cf_dia = st.number_input("Dia Vencimento", 1, 31, 10)
                cf_cat = st.selectbox("Categoria", ["Casa", "Serviços", "Pessoal", "Cartão de Crédito", "Emprestimo", "Outros"])
                if st.button("Salvar CF"):
                    finance_controller.salvar_conta_fixa(st.session_state['usuario_atual'], cf_nome, cf_val, cf_dia, cf_cat)
                    st.rerun()
        
        # Listagem das Contas
        contas = finance_controller.listar_contas_fixas(st.session_state['usuario_atual'])
        if not contas.empty:
             for _, row in contas.iterrows():
                ja_pagou = finance_controller.verificar_pagamento_conta(st.session_state['usuario_atual'], row['nome'], sel_mes, sel_ano)
                
                with st.container(border=True):
                    c_i, c_p, c_o = st.columns([3, 2, 1])
                    
                    check = "✅" if ja_pagou else "⏳"
                    # Define a data de pagamento para ser salva no banco
                    dia_venc = int(row['dia_vencimento'])
                    # Correção para fevereiro/meses curtos
                    if sel_mes == 2 and dia_venc > 28: dia_venc = 28
                    elif dia_venc > 30: dia_venc = 30
                    
                    data_pagamento = datetime(sel_ano, sel_mes, dia_venc)

                    c_i.markdown(f"{check} **{row['nome']}** (Dia {row['dia_vencimento']})<br>R$ {float(row['valor_previsto']):.2f}", unsafe_allow_html=True)
                    
                    if ja_pagou: 
                        c_p.button("PAGO", disabled=True, key=f"pgk_{row['id']}")
                    else:
                        if c_p.button("Pagar", key=f"pg_{row['id']}"):
                            finance_controller.pagar_conta_fixa(
                                st.session_state['usuario_atual'], 
                                row['nome'], 
                                float(row['valor_previsto']), 
                                data_pagamento, 
                                row['categoria']
                            )
                            st.rerun()
                            
                    with c_o.popover("⚙️"):
                        if st.button("Edit", key=f"edcf_{row['id']}"): 
                            st.session_state['edit_cf_id'] = row['id']
                            st.rerun()
                        if st.button("Del", key=f"dlcf_{row['id']}"): 
                            finance_controller.excluir_conta_fixa(row['id'])
                            st.rerun()
        else:
            st.info("Nenhuma conta fixa cadastrada.")