import hashlib
import pandas as pd
from datetime import datetime
from models import database
from controllers import vehicle_controller

# ... (MANTENHA AS FUNÇÕES DE LOGIN, CADASTRO, TRANSAÇÕES, EXTRATO, RESUMO IGUAIS) ...
def realizar_login(username, senha):
    database.inicializar_db()
    user_data = database.buscar_usuario(username.strip().lower())
    if not user_data.empty:
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        if user_data.iloc[0]['senha'] == senha_hash:
            return user_data.iloc[0]['nome']
    return None

def cadastrar_usuario(username, nome, email, contato, senha):
    database.inicializar_db()
    df_users = database.carregar_dados('usuarios')
    user_clean = username.strip().lower()
    if user_clean in df_users['username'].values: return False, "Usuário existe!"
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    novo = {'username': user_clean, 'nome': nome, 'email': email, 'contato': contato, 'senha': senha_hash}
    return database.salvar_no_excel(pd.concat([df_users, pd.DataFrame([novo])], ignore_index=True), 'usuarios')

def adicionar_transacao(username, data, tipo, categoria, valor, metodo, descricao):
    df = database.carregar_dados('transacoes')
    novo = {'id': database.gerar_id(), 'username': username, 'data': data, 'tipo': tipo, 'categoria': categoria, 'valor': float(valor), 'metodo_pagamento': metodo, 'descricao': descricao}
    return database.salvar_no_excel(pd.concat([df, pd.DataFrame([novo])], ignore_index=True), 'transacoes')

def excluir_transacao(id_transacao):
    return database.excluir_registro('transacoes', 'id', id_transacao)

def obter_transacao(id_transacao):
    df = database.carregar_dados('transacoes')
    filtro = df[df['id'] == id_transacao]
    return filtro.iloc[0] if not filtro.empty else None

def atualizar_transacao(id_transacao, data, categoria, valor, metodo, descricao):
    dados = {'data': data, 'categoria': categoria, 'valor': float(valor), 'metodo_pagamento': metodo, 'descricao': descricao}
    return database.atualizar_registro('transacoes', 'id', id_transacao, dados)

def obter_extrato(username, mes=None, ano=None):
    df = database.carregar_dados('transacoes')
    df = df[df['username'] == username]
    df['data'] = pd.to_datetime(df['data'])
    if mes and ano:
        df = df[(df['data'].dt.month == mes) & (df['data'].dt.year == ano)]
    return df.sort_values(by='data', ascending=False)

def calcular_resumo(username, mes=None, ano=None):
    df_user = obter_extrato(username, mes, ano)
    rec_fin = df_user[df_user['tipo'] == 'Receita']['valor'].sum() if not df_user.empty else 0.0
    desp_fin = df_user[df_user['tipo'] == 'Despesa']['valor'].sum() if not df_user.empty else 0.0
    
    df_veic = database.carregar_dados('veiculos')
    user_veiculos = df_veic[df_veic['username'] == username]['id'].tolist()
    lucro_viagens = 0.0
    if user_veiculos:
        df_viagens = database.carregar_dados('viagens')
        if not df_viagens.empty and 'lucro_liquido_calc' in df_viagens.columns:
            df_viagens['data'] = pd.to_datetime(df_viagens['data'])
            viagens_user = df_viagens[df_viagens['veiculo_id'].isin(user_veiculos)]
            if mes and ano:
                viagens_user = viagens_user[(viagens_user['data'].dt.month == mes) & (viagens_user['data'].dt.year == ano)]
            lucro_viagens = viagens_user['lucro_liquido_calc'].sum()

    total_receitas = rec_fin + lucro_viagens
    saldo_mes = total_receitas - desp_fin
    return total_receitas, desp_fin, saldo_mes, lucro_viagens

def obter_dados_grafico(username, mes=None, ano=None):
    df_user = obter_extrato(username, mes, ano)
    despesas = df_user[df_user['tipo'] == 'Despesa']
    if despesas.empty: return None
    return despesas.groupby('categoria')['valor'].sum().reset_index()

# ... (MANTENHA ALERTAS FROTA, CONTAS FIXAS...)
def obter_alertas_frota(username):
    df_v = database.carregar_dados('veiculos')
    meus_veiculos = df_v[df_v['username'] == username]
    alertas_lic = []
    alertas_man = []
    hoje = datetime.now()
    
    for _, veiculo in meus_veiculos.iterrows():
        try:
            data_lic = pd.to_datetime(veiculo['data_licenciamento'])
            if not pd.isna(data_lic):
                dias = (data_lic - hoje).days
                alertas_lic.append({'veiculo': veiculo['nome'], 'placa': veiculo['placa'], 'dias': dias + 1, 'valor': veiculo['valor_licenciamento'], 'vencimento_str': data_lic.strftime('%d/%m/%Y')})
        except: pass
        
        df_m = database.carregar_dados('manutencao')
        manuts = df_m[df_m['veiculo_id'] == veiculo['id']]
        km_atual = float(veiculo['km_atual'])
        for _, m in manuts.iterrows():
            km_falta = (float(m['km_ultima_troca']) + float(m['km_intervalo'])) - km_atual
            data_fmt = vehicle_controller.formatar_data_mes_ano(m['data_ultima_troca'])
            alertas_man.append({'veiculo': veiculo['nome'], 'item': m['item'], 'km_faltante': km_falta, 'ultima_data': data_fmt})
    return alertas_lic, alertas_man

def salvar_conta_fixa(username, nome, valor, dia, categoria):
    df = database.carregar_dados('contas_fixas')
    novo = {'id': database.gerar_id(), 'username': username, 'nome': nome, 'valor_previsto': float(valor), 'dia_vencimento': int(dia), 'categoria': categoria}
    return database.salvar_no_excel(pd.concat([df, pd.DataFrame([novo])], ignore_index=True), 'contas_fixas')

def atualizar_conta_fixa(id_conta, nome, valor, dia, categoria):
    dados = {'nome': nome, 'valor_previsto': float(valor), 'dia_vencimento': int(dia), 'categoria': categoria}
    return database.atualizar_registro('contas_fixas', 'id', id_conta, dados)

def listar_contas_fixas(username):
    df = database.carregar_dados('contas_fixas')
    return df[df['username'] == username].sort_values(by='dia_vencimento')

def excluir_conta_fixa(id_conta):
    return database.excluir_registro('contas_fixas', 'id', id_conta)

def verificar_pagamento_conta(username, nome_conta, mes, ano):
    df = obter_extrato(username, mes, ano)
    pagamento = df[df['descricao'] == f"Pgto: {nome_conta}"]
    return not pagamento.empty

def pagar_conta_fixa(username, conta_nome, valor_pago, data_pagamento, categoria):
    return adicionar_transacao(username, data_pagamento, "Despesa", categoria, valor_pago, "Conta Fixa", f"Pgto: {conta_nome}")

# --- METAS (ATUALIZADO) ---

def salvar_meta(username, nome, valor_alvo, data_limite, rendimento):
    df = database.carregar_dados('metas')
    novo = {
        'id': database.gerar_id(), 'username': username, 'nome': nome, 
        'valor_alvo': float(valor_alvo), 'valor_guardado': 0.0, 
        'data_limite': data_limite, 'descricao': "", 
        'rendimento_mensal': float(rendimento),
        'data_ultimo_rendimento': pd.NaT # Começa vazio
    }
    return database.salvar_no_excel(pd.concat([df, pd.DataFrame([novo])], ignore_index=True), 'metas')

def atualizar_meta_saldo(id_meta, novo_saldo, novo_nome=None, novo_rendimento=None):
    dados = {'valor_guardado': float(novo_saldo)}
    if novo_nome: dados['nome'] = novo_nome
    if novo_rendimento is not None: dados['rendimento_mensal'] = float(novo_rendimento)
    return database.atualizar_registro('metas', 'id', id_meta, dados)

def listar_metas(username):
    df = database.carregar_dados('metas')
    return df[df['username'] == username]

def excluir_meta(id_meta):
    return database.excluir_registro('metas', 'id', id_meta)

def depositar_meta(id_meta, valor_deposito, username):
    df_metas = database.carregar_dados('metas')
    idx = df_metas.index[df_metas['id'] == id_meta].tolist()[0]
    novo_total = float(df_metas.at[idx, 'valor_guardado']) + float(valor_deposito)
    database.atualizar_registro('metas', 'id', id_meta, {'valor_guardado': novo_total})
    return adicionar_transacao(username, datetime.now(), "Despesa", "Metas/Investimento", valor_deposito, "Transferência", f"Depósito Meta: {df_metas.at[idx, 'nome']}")

# NOVO: Verifica se o rendimento já foi aplicado NESTE mês atual (data de hoje)
def verificar_rendimento_aplicado(id_meta):
    df_metas = database.carregar_dados('metas')
    meta = df_metas[df_metas['id'] == id_meta].iloc[0]
    
    ultima_data = pd.to_datetime(meta.get('data_ultimo_rendimento'))
    if pd.isna(ultima_data): return False
    
    hoje = datetime.now()
    # Se a última vez foi no mesmo mês e ano de hoje, então já aplicou
    if ultima_data.month == hoje.month and ultima_data.year == hoje.year:
        return True
    return False

# ATUALIZADO: Aplica e salva a data
def aplicar_rendimento_meta(id_meta):
    df_metas = database.carregar_dados('metas')
    meta = df_metas[df_metas['id'] == id_meta].iloc[0]
    
    saldo_atual = float(meta['valor_guardado'])
    rendimento_pct = float(meta.get('rendimento_mensal', 0.0))
    
    if rendimento_pct > 0:
        ganho = saldo_atual * (rendimento_pct / 100)
        novo_total = saldo_atual + ganho
        
        # Atualiza saldo E data
        database.atualizar_registro('metas', 'id', id_meta, {
            'valor_guardado': novo_total,
            'data_ultimo_rendimento': datetime.now() # Marca que foi hoje
        })
        return True, f"Rendimento de R$ {ganho:.2f} aplicado!"
    return False, "Sem rendimento configurado."