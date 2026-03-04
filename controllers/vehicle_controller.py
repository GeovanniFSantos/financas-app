import pandas as pd
from datetime import datetime
from models import database

# --- FUNÇÕES AUXILIARES ---
def formatar_data_mes_ano(data_str):
    try:
        if pd.isna(data_str): return "-"
        dt = pd.to_datetime(data_str)
        meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        return f"{meses[dt.month]} {dt.year}"
    except:
        return str(data_str)

# --- VEÍCULOS (CRUD MySQL) ---

def salvar_veiculo(username, nome, tipo, placa, data_lic, valor_lic, km_atual, media_consumo, valor_litro):
    user_id = database.get_user_id(username)
    if not user_id: return False, "Usuário não encontrado"
    
    query = """
    INSERT INTO veiculos (user_id, nome, tipo, placa, data_licenciamento, valor_licenciamento, km_atual, media_consumo, valor_litro_combustivel)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    valores = (user_id, nome, tipo, placa, data_lic, valor_lic, km_atual, media_consumo, valor_litro)
    return database.executar_query(query, valores)

def listar_veiculos(username):
    user_id = database.get_user_id(username)
    if not user_id: return pd.DataFrame()
    
    query = "SELECT * FROM veiculos WHERE user_id = %s"
    df = database.carregar_query(query, (user_id,))
    
    if not df.empty:
        cols_float = ['valor_licenciamento', 'km_atual', 'media_consumo', 'valor_litro_combustivel']
        for col in cols_float:
            df[col] = df[col].astype(float)
    return df

# --- AS FUNÇÕES QUE FALTAVAM (OBTER e ATUALIZAR VEÍCULO) ---
def obter_veiculo(id_veiculo):
    """Busca um veículo específico para edição"""
    query = "SELECT * FROM veiculos WHERE id = %s"
    df = database.carregar_query(query, (id_veiculo,))
    return df.iloc[0] if not df.empty else None

def atualizar_veiculo(id_veiculo, nome, tipo, placa, data_lic, valor_lic, km_atual, media_consumo, valor_litro):
    """Salva a edição do veículo"""
    query = """
    UPDATE veiculos 
    SET nome=%s, tipo=%s, placa=%s, data_licenciamento=%s, valor_licenciamento=%s, km_atual=%s, media_consumo=%s, valor_litro_combustivel=%s 
    WHERE id=%s
    """
    valores = (nome, tipo, placa, data_lic, valor_lic, km_atual, media_consumo, valor_litro, id_veiculo)
    return database.executar_query(query, valores)
# -----------------------------------------------------------

def excluir_veiculo(id_veiculo):
    query = "DELETE FROM veiculos WHERE id = %s"
    return database.executar_query(query, (id_veiculo,))

def atualizar_km_veiculo(veiculo_id, km_rodados):
    query_select = "SELECT km_atual FROM veiculos WHERE id = %s"
    df = database.carregar_query(query_select, (veiculo_id,))
    if not df.empty:
        km_atual = float(df.iloc[0]['km_atual'])
        novo_km = km_atual + float(km_rodados)
        query_update = "UPDATE veiculos SET km_atual = %s WHERE id = %s"
        database.executar_query(query_update, (novo_km, veiculo_id))

# --- MANUTENÇÃO (CRUD MySQL) ---

def salvar_manutencao(veiculo_id, item, km_intervalo, custo_estimado, km_ultima_troca, data_ultima_troca):
    query = """
    INSERT INTO manutencao (veiculo_id, item, km_intervalo, custo_estimado, km_ultima_troca, data_ultima_troca)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    return database.executar_query(query, (veiculo_id, item, km_intervalo, custo_estimado, km_ultima_troca, data_ultima_troca))

def listar_manutencoes(veiculo_id):
    query = "SELECT * FROM manutencao WHERE veiculo_id = %s"
    df = database.carregar_query(query, (veiculo_id,))
    if not df.empty:
        df['km_intervalo'] = df['km_intervalo'].astype(float)
        df['km_ultima_troca'] = df['km_ultima_troca'].astype(float)
        df['custo_estimado'] = df['custo_estimado'].astype(float)
    return df

def obter_manutencao(id_manutencao):
    query = "SELECT * FROM manutencao WHERE id = %s"
    df = database.carregar_query(query, (id_manutencao,))
    return df.iloc[0] if not df.empty else None

def atualizar_manutencao(id_manutencao, item, km_intervalo, custo, km_troca, data_troca):
    query = """
    UPDATE manutencao 
    SET item=%s, km_intervalo=%s, custo_estimado=%s, km_ultima_troca=%s, data_ultima_troca=%s 
    WHERE id=%s
    """
    return database.executar_query(query, (item, km_intervalo, custo, km_troca, data_troca, id_manutencao))

def excluir_manutencao(id_manutencao):
    return database.executar_query("DELETE FROM manutencao WHERE id = %s", (id_manutencao,))

def registrar_troca_manutencao(id_manutencao, nova_km, nova_data):
    query = "UPDATE manutencao SET km_ultima_troca=%s, data_ultima_troca=%s WHERE id=%s"
    return database.executar_query(query, (nova_km, nova_data, id_manutencao))

# --- VIAGENS / DIÁRIO ---

def salvar_viagem_diaria(username, veiculo_id, data, km_rodados, faturamento, qtd_entregas, gastos_extras, desc_extra):
    query_veic = "SELECT media_consumo, valor_litro_combustivel FROM veiculos WHERE id = %s"
    df_veic = database.carregar_query(query_veic, (veiculo_id,))
    
    if df_veic.empty: return False, "Veículo não encontrado"
    
    try:
        media = float(df_veic.iloc[0]['media_consumo'])
        preco_gas = float(df_veic.iloc[0]['valor_litro_combustivel'])
    except:
        media = 30.0 
        preco_gas = 5.00

    custo_gasolina = (float(km_rodados) / media) * preco_gas if media > 0 else 0
    custo_depreciacao = float(km_rodados) * 0.10 
    lucro_liquido = float(faturamento) - custo_gasolina - custo_depreciacao - float(gastos_extras)
    
    query_insert = """
    INSERT INTO viagens (veiculo_id, data, km_rodados, faturamento, qtd_entregas, gastos_extras, descricao_extra, custo_gasolina_calc, custo_depreciacao_calc, lucro_liquido_calc)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    sucesso, msg = database.executar_query(query_insert, (veiculo_id, data, km_rodados, faturamento, qtd_entregas, gastos_extras, desc_extra, custo_gasolina, custo_depreciacao, lucro_liquido))
    
    if sucesso:
        atualizar_km_veiculo(veiculo_id, km_rodados)
        return True, f"✅ Salvo! Lucro: R$ {lucro_liquido:.2f}"
    
    return False, msg

def listar_viagens(veiculo_id):
    query = "SELECT * FROM viagens WHERE veiculo_id = %s ORDER BY data DESC"
    df = database.carregar_query(query, (veiculo_id,))
    if not df.empty:
        cols_float = ['km_rodados', 'faturamento', 'lucro_liquido_calc', 'custo_gasolina_calc']
        for col in cols_float:
            if col in df.columns:
                df[col] = df[col].astype(float)
        df['data'] = pd.to_datetime(df['data'])
    return df

def excluir_viagem(id_viagem):
    return database.executar_query("DELETE FROM viagens WHERE id = %s", (id_viagem,))

def obter_resumo_viagens(veiculo_id):
    df = listar_viagens(veiculo_id)
    if df.empty: return 0, 0, 0
    
    fat = df['faturamento'].sum()
    lucro = df['lucro_liquido_calc'].sum()
    km = df['km_rodados'].sum()
    return fat, lucro, km