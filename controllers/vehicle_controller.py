import pandas as pd
from models import database
from datetime import datetime
import uuid

# Helper para traduzir mês
def formatar_data_mes_ano(data_obj):
    if pd.isna(data_obj) or str(data_obj) == 'NaT': return "N/D"
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    try:
        dt = pd.to_datetime(data_obj)
        return f"{meses[dt.month]} {dt.year}"
    except:
        return str(data_obj)

def gerar_id(): return str(uuid.uuid4())[:8]

# ATUALIZADO: Recebe placa, data_lic, valor_lic
def salvar_veiculo(username, nome, tipo, placa, data_lic, valor_lic, km_atual, media_consumo, valor_litro):
    df_veiculos = database.carregar_dados('veiculos')
    novo = {
        'id': gerar_id(), 'username': username, 'nome': nome, 'tipo': tipo,
        'placa': placa.upper(), 'data_licenciamento': data_lic, 'valor_licenciamento': float(valor_lic),
        'km_atual': float(km_atual), 'media_consumo': float(media_consumo),
        'valor_litro_combustivel': float(valor_litro)
    }
    return database.salvar_no_excel(pd.concat([df_veiculos, pd.DataFrame([novo])], ignore_index=True), 'veiculos')

def atualizar_veiculo(veiculo_id, nome, tipo, placa, data_lic, valor_lic, km_atual, media, litro):
    dados = {
        'nome': nome, 'tipo': tipo, 'placa': placa.upper(),
        'data_licenciamento': data_lic, 'valor_licenciamento': float(valor_lic),
        'km_atual': float(km_atual), 'media_consumo': float(media), 'valor_litro_combustivel': float(litro)
    }
    return database.atualizar_registro('veiculos', 'id', veiculo_id, dados)

# ATUALIZADO: Recebe data_ultima_troca
def salvar_manutencao(veiculo_id, item, km_intervalo, custo_estimado, km_ultima_troca, data_ultima_troca):
    df = database.carregar_dados('manutencao')
    novo = {
        'id': gerar_id(), 'veiculo_id': veiculo_id, 'item': item,
        'km_intervalo': float(km_intervalo), 'custo_estimado': float(custo_estimado),
        'km_ultima_troca': float(km_ultima_troca),
        'data_ultima_troca': data_ultima_troca
    }
    return database.salvar_no_excel(pd.concat([df, pd.DataFrame([novo])], ignore_index=True), 'manutencao')

def atualizar_manutencao(manut_id, item, intervalo, custo, ultima_km_troca, ultima_data_troca):
    dados = {
        'item': item, 'km_intervalo': float(intervalo), 'custo_estimado': float(custo),
        'km_ultima_troca': float(ultima_km_troca), 'data_ultima_troca': ultima_data_troca
    }
    return database.atualizar_registro('manutencao', 'id', manut_id, dados)

# ... (MANTENHA AS OUTRAS FUNÇÕES: listar, excluir, obter...)
def listar_veiculos(username):
    df = database.carregar_dados('veiculos')
    return df[df['username'] == username]

def excluir_veiculo(veiculo_id):
    database.excluir_registro('manutencao', 'veiculo_id', veiculo_id)
    database.excluir_registro('viagens', 'veiculo_id', veiculo_id)
    return database.excluir_registro('veiculos', 'id', veiculo_id)

def listar_manutencoes(veiculo_id):
    df = database.carregar_dados('manutencao')
    return df[df['veiculo_id'] == veiculo_id]

def excluir_manutencao(manut_id):
    return database.excluir_registro('manutencao', 'id', manut_id)

def obter_veiculo(veiculo_id):
    df = database.carregar_dados('veiculos')
    filtro = df[df['id'] == veiculo_id]
    return filtro.iloc[0] if not filtro.empty else None

def obter_manutencao(manut_id):
    df = database.carregar_dados('manutencao')
    filtro = df[df['id'] == manut_id]
    return filtro.iloc[0] if not filtro.empty else None