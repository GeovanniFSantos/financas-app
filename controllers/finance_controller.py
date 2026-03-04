import hashlib
import pandas as pd
from datetime import datetime
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
    user_data = database.buscar_usuario(login_limpo) # Agora busca no MySQL
    
    if not user_data.empty:
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        senha_banco = str(user_data.iloc[0]['senha'])
        
        if senha_banco == senha_hash:
            return user_data.iloc[0]['username'], user_data.iloc[0]['nome']
    return None, None

def cadastrar_usuario(username, nome, email, contato, senha):
    user_clean = username.strip().lower()
    
    # Verifica duplicidade
    if not database.buscar_usuario(user_clean).empty:
        return False, "Usuário já existe!"
        
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    query = """
    INSERT INTO usuarios (username, nome, email, contato, senha) 
    VALUES (%s, %s, %s, %s, %s)
    """
    return database.executar_query(query, (user_clean, nome, email, contato, senha_hash))

def obter_dados_usuario(username):
    user = database.buscar_usuario(username)
    return user.iloc[0] if not user.empty else None

def atualizar_perfil(username, novo_nome, novo_email, novo_contato, nova_data_nascimento):
    query = """
    UPDATE usuarios 
    SET nome=%s, email=%s, contato=%s, data_nascimento=%s 
    WHERE username=%s
    """
    return database.executar_query(query, (novo_nome, novo_email, novo_contato, nova_data_nascimento, username))

def alterar_senha(username, nova_senha):
    senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
    query = "UPDATE usuarios SET senha=%s WHERE username=%s"
    return database.executar_query(query, (senha_hash, username))

def salvar_foto_perfil(username, base64_foto):
    # MySQL LONGTEXT aguenta a foto tranquila!
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
    query = "DELETE FROM transacoes WHERE id = %s"
    return database.executar_query(query, (id_transacao,))

def obter_transacao(id_transacao):
    query = "SELECT * FROM transacoes WHERE id = %s"
    df = database.carregar_query(query, (id_transacao,))
    return df.iloc[0] if not df.empty else None

def atualizar_transacao(id_transacao, data, categoria, valor, metodo, descricao):
    query = """
    UPDATE transacoes 
    SET data=%s, categoria=%s, valor=%s, metodo_pagamento=%s, descricao=%s 
    WHERE id=%s
    """
    return database.executar_query(query, (data, categoria, valor, metodo, descricao, id_transacao))

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
    # Converter tipos decimais para float (pandas às vezes traz como Decimal object)
    if not df.empty:
        df['valor'] = df['valor'].astype(float)
        df['data'] = pd.to_datetime(df['data'])
    return df

def calcular_resumo(username, mes=None, ano=None):
    df_user = obter_extrato(username, mes, ano)
    
    rec_fin = df_user[df_user['tipo'] == 'Receita']['valor'].sum() if not df_user.empty else 0.0
    desp_fin = df_user[df_user['tipo'] == 'Despesa']['valor'].sum() if not df_user.empty else 0.0
    
    # Busca veículos do usuário
    user_id = database.get_user_id(username)
    lucro_viagens = 0.0
    
    if user_id:
        query_veic = "SELECT id FROM veiculos WHERE user_id = %s"
        df_veic = database.carregar_query(query_veic, (user_id,))
        ids_veiculos = df_veic['id'].tolist() if not df_veic.empty else []
        
        if ids_veiculos:
            # Query complexa para somar lucro de viagens filtrando por data
            placeholders = ', '.join(['%s'] * len(ids_veiculos))
            query_viagem = f"SELECT * FROM viagens WHERE veiculo_id IN ({placeholders})"
            params = ids_veiculos
            
            df_viagens = database.carregar_query(query_viagem, tuple(params))
            
            if not df_viagens.empty:
                df_viagens['data'] = pd.to_datetime(df_viagens['data'])
                df_viagens['lucro_liquido_calc'] = df_viagens['lucro_liquido_calc'].astype(float)
                
                if mes and ano:
                    df_viagens = df_viagens[(df_viagens['data'].dt.month == mes) & (df_viagens['data'].dt.year == ano)]
                
                lucro_viagens = df_viagens['lucro_liquido_calc'].sum()

    total_receitas = rec_fin + lucro_viagens
    saldo_mes = total_receitas - desp_fin
    return total_receitas, desp_fin, saldo_mes, lucro_viagens

def obter_dados_grafico(username, mes=None, ano=None):
    df_user = obter_extrato(username, mes, ano)
    if df_user.empty: return None
    despesas = df_user[df_user['tipo'] == 'Despesa']
    if despesas.empty: return None
    return despesas.groupby('categoria')['valor'].sum().reset_index()

# --- FROTA (Veículos e Manutenção) ---
def obter_alertas_frota(username):
    user_id = database.get_user_id(username)
    alertas_lic, alertas_man = [], []
    if not user_id: return alertas_lic, alertas_man
    
    # Busca Veículos
    query_v = "SELECT * FROM veiculos WHERE user_id = %s"
    df_v = database.carregar_query(query_v, (user_id,))
    
    hoje = datetime.now()
    
    for _, veiculo in df_v.iterrows():
        # Licenciamento
        if veiculo['data_licenciamento']:
            data_lic = pd.to_datetime(veiculo['data_licenciamento'])
            dias = (data_lic - hoje).days
            alertas_lic.append({'veiculo': veiculo['nome'], 'placa': veiculo['placa'], 'dias': dias + 1, 'valor': float(veiculo['valor_licenciamento'] or 0), 'vencimento_str': data_lic.strftime('%d/%m/%Y')})
            
        # Manutenção
        query_m = "SELECT * FROM manutencao WHERE veiculo_id = %s"
        df_m = database.carregar_query(query_m, (veiculo['id'],))
        
        km_atual = float(veiculo['km_atual'])
        for _, m in df_m.iterrows():
            km_falta = (float(m['km_ultima_troca']) + float(m['km_intervalo'])) - km_atual
            data_fmt = _formatar_data_visual(m['data_ultima_troca'])
            alertas_man.append({'veiculo': veiculo['nome'], 'item': m['item'], 'km_faltante': km_falta, 'ultima_data': data_fmt})
            
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
    query = "DELETE FROM contas_fixas WHERE id = %s"
    return database.executar_query(query, (id_conta,))

def verificar_pagamento_conta(username, nome_conta, mes, ano):
    df = obter_extrato(username, mes, ano)
    if df.empty: return False
    pagamento = df[df['descricao'] == f"Pgto: {nome_conta}"]
    return not pagamento.empty

def pagar_conta_fixa(username, conta_nome, valor_pago, data_pagamento, categoria):
    return adicionar_transacao(username, data_pagamento, "Despesa", categoria, valor_pago, "Conta Fixa", f"Pgto: {conta_nome}")

# --- METAS ---
def salvar_meta(username, nome, valor_alvo, data_limite, rendimento):
    user_id = database.get_user_id(username)
    query = """
    INSERT INTO metas (user_id, nome, valor_alvo, valor_guardado, data_limite, rendimento_mensal) 
    VALUES (%s, %s, %s, 0, %s, %s)
    """
    return database.executar_query(query, (user_id, nome, valor_alvo, data_limite, rendimento))

def atualizar_meta_saldo(id_meta, novo_saldo, novo_nome=None, novo_rendimento=None):
    # Atualiza saldo
    query = "UPDATE metas SET valor_guardado = %s WHERE id = %s"
    database.executar_query(query, (novo_saldo, id_meta))
    
    if novo_nome: database.executar_query("UPDATE metas SET nome = %s WHERE id = %s", (novo_nome, id_meta))
    if novo_rendimento is not None: database.executar_query("UPDATE metas SET rendimento_mensal = %s WHERE id = %s", (novo_rendimento, id_meta))
    return True, "Atualizado"

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
    # 1. Pega saldo atual no banco
    df = database.carregar_query("SELECT valor_guardado, nome FROM metas WHERE id=%s", (id_meta,))
    saldo_atual = float(df.iloc[0]['valor_guardado'])
    nome_meta = df.iloc[0]['nome']
    
    # 2. Atualiza
    novo_saldo = saldo_atual + float(valor_deposito)
    database.executar_query("UPDATE metas SET valor_guardado=%s WHERE id=%s", (novo_saldo, id_meta))
    
    # 3. Lança despesa
    return adicionar_transacao(username, datetime.now(), "Despesa", "Metas/Investimento", valor_deposito, "Transferência", f"Depósito Meta: {nome_meta}")

def verificar_rendimento_aplicado(id_meta):
    df = database.carregar_query("SELECT data_ultimo_rendimento FROM metas WHERE id=%s", (id_meta,))
    ultima_data = pd.to_datetime(df.iloc[0]['data_ultimo_rendimento'])
    if pd.isna(ultima_data): return False
    hoje = datetime.now()
    return (ultima_data.month == hoje.month and ultima_data.year == hoje.year)

def aplicar_rendimento_meta(id_meta):
    df = database.carregar_query("SELECT valor_guardado, rendimento_mensal FROM metas WHERE id=%s", (id_meta,))
    saldo = float(df.iloc[0]['valor_guardado'])
    rend = float(df.iloc[0]['rendimento_mensal'] or 0)
    
    if rend > 0:
        ganho = saldo * (rend / 100)
        novo_saldo = saldo + ganho
        database.executar_query("UPDATE metas SET valor_guardado=%s, data_ultimo_rendimento=NOW() WHERE id=%s", (novo_saldo, id_meta))
        return True, f"Rendeu R$ {ganho:.2f}"
    return False, "Sem rendimento"