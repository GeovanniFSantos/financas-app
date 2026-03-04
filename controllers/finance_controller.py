import hashlib
import pandas as pd
from datetime import datetime
from datetime import date
import calendar 
import urllib.parse
from models import database


# --- AUXILIARES ---
def _formatar_data_visual(data):
    try:
        if pd.isna(data): return "-"
        dt = pd.to_datetime(data)
        meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        return f"{meses[dt.month]} {dt.year}"
    except: return str(data)

# --- LOGIN ---
def realizar_login(login_input, senha):
    login_limpo = login_input.strip().lower()
    user_data = database.buscar_usuario(login_limpo)
    
    if not user_data.empty:
        usuario = user_data.iloc[0]
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        
        if str(usuario['senha']) == senha_hash:
            # 1. VERIFICA STATUS MANUAL (SUSPENSO)
            if usuario['status_conta'] == 'suspenso':
                return "suspenso", None, None
            
            # 2. VERIFICA DATA DE EXPIRAÇÃO (BLOQUEIO AUTOMÁTICO)
            if usuario['data_expiracao']:
                if date.today() > usuario['data_expiracao']:
                    return "expirado", None, None
            
            return usuario['username'], usuario['nome'], usuario['nivel_acesso']
            
    return None, None, None


def cadastrar_usuario(username, nome, email, contato, senha):
    user_clean = username.strip().lower()
    if not database.buscar_usuario(user_clean).empty:
        return False, "Usuário já existe!"
        
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    query = "INSERT INTO usuarios (username, nome, email, contato, senha) VALUES (%s, %s, %s, %s, %s)"
    return database.executar_query(query, (user_clean, nome, email, contato, senha_hash))

# --- PERFIL ---
def obter_dados_usuario(username):
    user = database.buscar_usuario(username)
    return user.iloc[0] if not user.empty else None

def atualizar_perfil(username, novo_nome, novo_email, novo_contato, nova_data_nascimento):
    query = "UPDATE usuarios SET nome=%s, email=%s, contato=%s, data_nascimento=%s WHERE username=%s"
    return database.executar_query(query, (novo_nome, novo_email, novo_contato, nova_data_nascimento, username))

def alterar_senha(username, nova_senha):
    senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
    query = "UPDATE usuarios SET senha=%s WHERE username=%s"
    return database.executar_query(query, (senha_hash, username))

def salvar_foto_perfil(username, base64_foto):
    query = "UPDATE usuarios SET foto_perfil=%s WHERE username=%s"
    return database.executar_query(query, (base64_foto, username))

# --- TRANSAÇÕES ---
def adicionar_transacao(username, data, tipo, categoria, valor, metodo, descricao):
    user_id = database.get_user_id(username)
    if not user_id: return False, "Usuário não encontrado"
    
    query = """
    INSERT INTO transacoes (user_id, data, tipo, categoria, valor, metodo_pagamento, descricao)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    return database.executar_query(query, (user_id, data, tipo, categoria, valor, metodo, descricao))

def excluir_transacao(id_transacao):
    return database.executar_query("DELETE FROM transacoes WHERE id = %s", (id_transacao,))

def obter_extrato(username, mes=None, ano=None):
    user_id = database.get_user_id(username)
    if not user_id: return pd.DataFrame()

    query = "SELECT * FROM transacoes WHERE user_id = %s"
    params = [user_id]
    
    if mes and ano:
        query += " AND MONTH(data) = %s AND YEAR(data) = %s"
        params.extend([mes, ano])
    
    query += " ORDER BY data DESC"
    
    df = database.carregar_query(query, tuple(params))
    if not df.empty:
        df['valor'] = df['valor'].astype(float)
        df['data'] = pd.to_datetime(df['data'])
    return df

# --- CÁLCULO DE RESUMO (AQUI ESTÁ A GRANDE MUDANÇA) ---
def calcular_resumo(username, mes, ano):
    user_id = database.get_user_id(username)
    if not user_id: return 0.0, 0.0, 0.0, 0.0

    # Define a data limite para o Saldo Acumulado (Último dia do mês selecionado)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    data_limite_str = f"{ano}-{mes}-{ultimo_dia}"

    # 1. DADOS DO MÊS (Para Receita e Despesa - Cards Verde/Vermelho)
    # Mostra o fechamento APENAS daquele mês
    query_mes = """
        SELECT tipo, SUM(valor) as total 
        FROM transacoes 
        WHERE user_id = %s AND MONTH(data) = %s AND YEAR(data) = %s 
        GROUP BY tipo
    """
    df_mes = database.carregar_query(query_mes, (user_id, mes, ano))
    
    rec_mes = df_mes[df_mes['tipo'] == 'Receita']['total'].sum() if not df_mes.empty else 0.0
    desp_mes = df_mes[df_mes['tipo'] == 'Despesa']['total'].sum() if not df_mes.empty else 0.0

    # 2. DADOS ACUMULADOS (Para o Saldo - Card Azul)
    # Soma tudo desde o começo até o final do mês selecionado
    query_acum = """
        SELECT tipo, SUM(valor) as total 
        FROM transacoes 
        WHERE user_id = %s AND data <= %s 
        GROUP BY tipo
    """
    df_acum = database.carregar_query(query_acum, (user_id, data_limite_str))
    
    rec_acum = df_acum[df_acum['tipo'] == 'Receita']['total'].sum() if not df_acum.empty else 0.0
    desp_acum = df_acum[df_acum['tipo'] == 'Despesa']['total'].sum() if not df_acum.empty else 0.0

    # 3. DADOS DAS VIAGENS (FROTA)
    # Precisamos separar o que é do Mês (para exibir custos) e o que é Acumulado (para o saldo)
    
    query_veic = "SELECT id FROM veiculos WHERE user_id = %s"
    df_veic = database.carregar_query(query_veic, (user_id,))
    ids_veiculos = df_veic['id'].tolist() if not df_veic.empty else []

    fat_viagens_mes = 0.0
    custos_viagens_mes = 0.0
    lucro_viagens_mes_card = 0.0 # Apenas informativo para o expander
    lucro_liquido_viagens_acumulado = 0.0 # Para o Saldo Final

    if ids_veiculos:
        placeholders = ', '.join(['%s'] * len(ids_veiculos))
        
        # A. Viagens do Mês (Para compor Receita/Despesa do Painel)
        query_v_mes = f"""
            SELECT faturamento, custo_gasolina_calc, custo_depreciacao_calc, gastos_extras, lucro_liquido_calc
            FROM viagens 
            WHERE veiculo_id IN ({placeholders}) AND MONTH(data) = %s AND YEAR(data) = %s
        """
        params_mes = ids_veiculos + [mes, ano]
        df_v_mes = database.carregar_query(query_v_mes, tuple(params_mes))
        
        if not df_v_mes.empty:
            for c in df_v_mes.columns: df_v_mes[c] = df_v_mes[c].astype(float)
            fat_viagens_mes = df_v_mes['faturamento'].sum()
            custos_viagens_mes = (df_v_mes['custo_gasolina_calc'].sum() + 
                                  df_v_mes['custo_depreciacao_calc'].sum() + 
                                  df_v_mes['gastos_extras'].sum())
            lucro_viagens_mes_card = df_v_mes['lucro_liquido_calc'].sum()

        # B. Viagens Acumuladas (Para compor o Saldo Real)
        query_v_acum = f"""
            SELECT SUM(lucro_liquido_calc) as total_lucro
            FROM viagens 
            WHERE veiculo_id IN ({placeholders}) AND data <= %s
        """
        params_acum = ids_veiculos + [data_limite_str]
        df_v_acum = database.carregar_query(query_v_acum, tuple(params_acum))
        
        if not df_v_acum.empty:
            lucro_liquido_viagens_acumulado = float(df_v_acum.iloc[0]['total_lucro'] or 0.0)

    # --- RESULTADOS FINAIS ---
    
    # Receita MENSAL (O que entrou bruto neste mês)
    total_receita_mes = rec_mes + fat_viagens_mes
    
    # Despesa MENSAL (O que saiu bruto neste mês)
    total_despesa_mes = desp_mes + custos_viagens_mes
    
    # SALDO ACUMULADO (A "Conta Bancária" Real: Tudo que sobrou até hoje)
    # (Receitas Manuais Acumuladas - Despesas Manuais Acumuladas) + (Lucro Líquido Acumulado das Viagens)
    saldo_acumulado_manual = rec_acum - desp_acum
    saldo_final_real = saldo_acumulado_manual + lucro_liquido_viagens_acumulado
    
    return total_receita_mes, total_despesa_mes, saldo_final_real, lucro_viagens_mes_card

def obter_dados_grafico(username, mes=None, ano=None):
    df_user = obter_extrato(username, mes, ano)
    if df_user.empty: return None
    despesas = df_user[df_user['tipo'] == 'Despesa']
    if despesas.empty: return None
    return despesas.groupby('categoria')['valor'].sum().reset_index()

# --- FROTA ---
def obter_alertas_frota(username):
    user_id = database.get_user_id(username)
    alertas_lic, alertas_man = [], []
    if not user_id: return alertas_lic, alertas_man
    
    query_v = "SELECT * FROM veiculos WHERE user_id = %s"
    df_v = database.carregar_query(query_v, (user_id,))
    hoje = datetime.now()
    
    for _, veiculo in df_v.iterrows():
        if veiculo['data_licenciamento']:
            data_lic = pd.to_datetime(veiculo['data_licenciamento'])
            dias = (data_lic - hoje).days
            alertas_lic.append({'veiculo': veiculo['nome'], 'valor': float(veiculo['valor_licenciamento'] or 0), 'dias': dias + 1})
            
        query_m = "SELECT * FROM manutencao WHERE veiculo_id = %s"
        df_m = database.carregar_query(query_m, (veiculo['id'],))
        km_atual = float(veiculo['km_atual'])
        for _, m in df_m.iterrows():
            km_falta = (float(m['km_ultima_troca']) + float(m['km_intervalo'])) - km_atual
            alertas_man.append({'veiculo': veiculo['nome'], 'item': m['item'], 'km_faltante': km_falta})
            
    return alertas_lic, alertas_man

# --- CONTAS FIXAS ---
def salvar_conta_fixa(username, nome, valor, dia, categoria):
    user_id = database.get_user_id(username)
    query = "INSERT INTO contas_fixas (user_id, nome, valor_previsto, dia_vencimento, categoria) VALUES (%s, %s, %s, %s, %s)"
    return database.executar_query(query, (user_id, nome, valor, dia, categoria))

def atualizar_conta_fixa(id_conta, nome, valor, dia, categoria):
    query = "UPDATE contas_fixas SET nome=%s, valor_previsto=%s, dia_vencimento=%s, categoria=%s WHERE id=%s"
    return database.executar_query(query, (nome, valor, dia, categoria, id_conta))

def listar_contas_fixas(username):
    user_id = database.get_user_id(username)
    if not user_id: return pd.DataFrame()
    query = "SELECT * FROM contas_fixas WHERE user_id = %s ORDER BY dia_vencimento"
    df = database.carregar_query(query, (user_id,))
    if not df.empty: df['valor_previsto'] = df['valor_previsto'].astype(float)
    return df

def excluir_conta_fixa(id_conta):
    return database.executar_query("DELETE FROM contas_fixas WHERE id = %s", (id_conta,))

def verificar_pagamento_conta(username, nome_conta, mes, ano):
    # Verifica pagamento no mês específico
    user_id = database.get_user_id(username)
    query = """
        SELECT id FROM transacoes 
        WHERE user_id = %s AND descricao = %s AND MONTH(data) = %s AND YEAR(data) = %s
    """
    df = database.carregar_query(query, (user_id, f"Pgto: {nome_conta}", mes, ano))
    return not df.empty

def pagar_conta_fixa(username, conta_nome, valor_pago, data_pagamento, categoria):
    return adicionar_transacao(username, data_pagamento, "Despesa", categoria, valor_pago, "Conta Fixa", f"Pgto: {conta_nome}")

# --- METAS (RENDIMENTO AJUSTADO) ---
def salvar_meta(username, nome, valor_alvo, data_limite, rendimento):
    user_id = database.get_user_id(username)
    query = "INSERT INTO metas (user_id, nome, valor_alvo, valor_guardado, data_limite, rendimento_mensal) VALUES (%s, %s, %s, 0, %s, %s)"
    return database.executar_query(query, (user_id, nome, valor_alvo, data_limite, rendimento))

def atualizar_meta_saldo(id_meta, novo_saldo, novo_nome=None, novo_rendimento=None):
    query = "UPDATE metas SET valor_guardado = %s, nome=%s, rendimento_mensal=%s WHERE id = %s"
    return database.executar_query(query, (novo_saldo, novo_nome, novo_rendimento, id_meta))

def listar_metas(username):
    user_id = database.get_user_id(username)
    if not user_id: return pd.DataFrame()
    query = "SELECT * FROM metas WHERE user_id = %s"
    df = database.carregar_query(query, (user_id,))
    if not df.empty:
        df['valor_guardado'] = df['valor_guardado'].astype(float)
        df['valor_alvo'] = df['valor_alvo'].astype(float)
    return df

def excluir_meta(id_meta):
    return database.executar_query("DELETE FROM metas WHERE id = %s", (id_meta,))

def depositar_meta(id_meta, valor_deposito, username):
    # 1. Pega saldo atual
    df = database.carregar_query("SELECT valor_guardado, nome FROM metas WHERE id=%s", (id_meta,))
    saldo_atual = float(df.iloc[0]['valor_guardado'])
    nome_meta = df.iloc[0]['nome']
    
    # 2. Atualiza Saldo
    novo_total = saldo_atual + float(valor_deposito)
    database.executar_query("UPDATE metas SET valor_guardado=%s WHERE id=%s", (novo_total, id_meta))
    
    # 3. Gera Despesa
    return adicionar_transacao(username, datetime.now(), "Despesa", "Metas/Investimento", valor_deposito, "Transferência", f"Depósito Meta: {nome_meta}")

def verificar_rendimento_aplicado(id_meta):
    # Verifica se já rendeu NO MÊS ATUAL (Calendário Real)
    df = database.carregar_query("SELECT data_ultimo_rendimento FROM metas WHERE id=%s", (id_meta,))
    if df.empty: return False
    
    ultima_data = pd.to_datetime(df.iloc[0]['data_ultimo_rendimento'])
    if pd.isna(ultima_data): return False
    
    hoje = datetime.now()
    # Se o mês e ano da última aplicação forem iguais ao de hoje, bloqueia.
    # Se virou o mês, libera.
    return (ultima_data.month == hoje.month and ultima_data.year == hoje.year)

def aplicar_rendimento_meta(id_meta):
    # Busca dados
    df = database.carregar_query("SELECT valor_guardado, rendimento_mensal FROM metas WHERE id=%s", (id_meta,))
    saldo = float(df.iloc[0]['valor_guardado'])
    rend_pct = float(df.iloc[0]['rendimento_mensal'] or 0)
    
    if rend_pct > 0:
        # Cálculo de Juros Compostos: Saldo * (1 + Taxa/100)
        # Ex: 10 reais * 1.17% = 0.117 de ganho. Novo saldo = 10.117
        ganho = saldo * (rend_pct / 100)
        novo_saldo = saldo + ganho
        
        # Atualiza o saldo E a data do rendimento para travar até o próximo mês
        database.executar_query("UPDATE metas SET valor_guardado=%s, data_ultimo_rendimento=NOW() WHERE id=%s", (novo_saldo, id_meta))
        return True, f"Rendimento de R$ {ganho:.2f} aplicado com sucesso!"
        
    return False, "Sem taxa de rendimento configurada."

def obter_dados_pizza(username, mes, ano):
    """Retorna os dados agrupados para o gráfico de pizza"""
    user_id = database.get_user_id(username)
    if not user_id: return pd.DataFrame()

    query = """
        SELECT categoria, SUM(valor) as total 
        FROM transacoes 
        WHERE user_id = %s AND tipo = 'Despesa' 
        AND MONTH(data) = %s AND YEAR(data) = %s
        GROUP BY categoria
    """
    df = database.carregar_query(query, (user_id, mes, ano))
    if not df.empty:
        df['total'] = df['total'].astype(float)
    return df

def gerar_link_whatsapp(receita, despesa, saldo, mes_nome, ano):
    """Gera um link que abre o WhatsApp com emojis que funcionam"""
    # Usando códigos de emoji que o WhatsApp reconhece bem
    texto = (
        f" *RESUMO FINANCEIRO - {mes_nome.upper()}/{ano}*\n\n"
        f" *Receita Bruta:* R$ {receita:,.2f}\n"
        f" *Custos/Despesas:* R$ {despesa:,.2f}\n"
        f"--------------------------\n"
        f" *LUCRO LÍQUIDO:* R$ {saldo:,.2f}\n\n"
        f" _Gerado pelo meu App Solução Sob Medida_"
    )
    
    texto_codificado = urllib.parse.quote(texto)
    return f"https://wa.me/?text={texto_codificado}"