import pandas as pd
from models import database
import uuid

def gerar_id(): return str(uuid.uuid4())[:8]

def salvar_diario(veiculo_id, data, km_rodados, faturamento, qtd_entregas, gastos_extras, desc_extra):
    df_veiculos = database.carregar_dados('veiculos')
    df_manut = database.carregar_dados('manutencao')
    df_viagens = database.carregar_dados('viagens')
    
    veiculo = df_veiculos[df_veiculos['id'] == veiculo_id].iloc[0]
    
    # Cálculos
    litros = km_rodados / float(veiculo['media_consumo'])
    gasolina = litros * float(veiculo['valor_litro_combustivel'])
    
    depreciacao = 0.0
    itens = df_manut[df_manut['veiculo_id'] == veiculo_id]
    for _, item in itens.iterrows():
        custo_km = float(item['custo_estimado']) / float(item['km_intervalo'])
        depreciacao += (custo_km * km_rodados)
        
    lucro = faturamento - (gasolina + depreciacao + gastos_extras)
    
    # Salva
    nova_viagem = {
        'id': gerar_id(), 'veiculo_id': veiculo_id, 'data': data,
        'km_rodados': km_rodados, 'faturamento': faturamento,
        'qtd_entregas': qtd_entregas, 'gastos_extras': gastos_extras,
        'custo_gasolina_calc': gasolina, 'custo_depreciacao_calc': depreciacao,
        'lucro_liquido_calc': lucro
    }
    
    # Atualiza KM Veículo
    idx = df_veiculos.index[df_veiculos['id'] == veiculo_id].tolist()[0]
    df_veiculos.at[idx, 'km_atual'] = float(veiculo['km_atual']) + km_rodados
    database.salvar_no_excel(df_veiculos, 'veiculos')
    
    return database.salvar_no_excel(pd.concat([df_viagens, pd.DataFrame([nova_viagem])], ignore_index=True), 'viagens')

def listar_viagens(veiculo_id):
    df = database.carregar_dados('viagens')
    if df.empty or 'custo_gasolina_calc' not in df.columns: return pd.DataFrame()
    return df[df['veiculo_id'] == veiculo_id]

def excluir_viagem(viagem_id):
    # Nota: Idealmente deveríamos estornar a KM do veículo, mas para simplificar vamos apenas deletar o registro financeiro por enquanto.
    return database.excluir_registro('viagens', 'id', viagem_id)

# ... (Mantenha o código anterior e ADICIONE isso no final) ...

def obter_viagem(viagem_id):
    df = database.carregar_dados('viagens')
    filtro = df[df['id'] == viagem_id]
    return filtro.iloc[0] if not filtro.empty else None

def atualizar_diario(viagem_id, nova_data, novo_km, novo_fat, nova_ent, novo_extra, nova_desc):
    # 1. Carregar dados ANTIGOS antes de mudar
    df_viagens = database.carregar_dados('viagens')
    viagem_antiga = df_viagens[df_viagens['id'] == viagem_id].iloc[0]
    
    veiculo_id = viagem_antiga['veiculo_id']
    km_antigo_da_viagem = float(viagem_antiga['km_rodados'])
    
    # 2. Carregar Veículo
    df_veiculos = database.carregar_dados('veiculos')
    idx_v = df_veiculos.index[df_veiculos['id'] == veiculo_id].tolist()[0]
    veiculo = df_veiculos.iloc[idx_v]
    
    # 3. Recalcular Custo (Gasolina e Depreciação) com os NOVOS dados
    media_consumo = float(veiculo['media_consumo'])
    preco_gasolina = float(veiculo['valor_litro_combustivel'])
    
    novo_custo_gas = (novo_km / media_consumo) * preco_gasolina
    
    # Depreciação
    df_manut = database.carregar_dados('manutencao')
    novo_custo_deprec = 0.0
    itens = df_manut[df_manut['veiculo_id'] == veiculo_id]
    for _, item in itens.iterrows():
        c_km = float(item['custo_estimado']) / float(item['km_intervalo'])
        novo_custo_deprec += (c_km * novo_km)
        
    novo_lucro = novo_fat - (novo_custo_gas + novo_custo_deprec + novo_extra)
    
    # 4. Ajustar Odômetro do Veículo (Matemática: Tira o velho, põe o novo)
    diferenca_km = novo_km - km_antigo_da_viagem
    novo_odometro_veiculo = float(veiculo['km_atual']) + diferenca_km
    
    # 5. Salvar Tudo
    dados_viagem_atualizados = {
        'data': nova_data,
        'km_rodados': novo_km,
        'faturamento': novo_fat,
        'qtd_entregas': nova_ent,
        'gastos_extras': novo_extra,
        'descricao_extra': nova_desc, # Caso tenha adicionado essa coluna
        'custo_gasolina_calc': novo_custo_gas,
        'custo_depreciacao_calc': novo_custo_deprec,
        'lucro_liquido_calc': novo_lucro
    }
    
    database.atualizar_registro('viagens', 'id', viagem_id, dados_viagem_atualizados)
    
    # Atualiza KM do veículo
    database.atualizar_registro('veiculos', 'id', veiculo_id, {'km_atual': novo_odometro_veiculo})
    
    return True, f"Viagem editada! Lucro recalculado: R$ {novo_lucro:.2f}"