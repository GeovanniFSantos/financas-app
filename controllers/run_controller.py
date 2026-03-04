import pandas as pd
from models import database
from controllers import vehicle_controller 


def salvar_diario(veiculo_id, data, km_rodados, faturamento, qtd_entregas, gastos_extras, desc_extra):
    
    # 1. Busca dados do veículo para calcular custos (MySQL)
    query_veic = "SELECT media_consumo, valor_litro_combustivel FROM veiculos WHERE id = %s"
    df_veic = database.carregar_query(query_veic, (veiculo_id,))
    
    if df_veic.empty: return False, "Veículo não encontrado"
    
    # Tratamento seguro de tipos
    try:
        media = float(df_veic.iloc[0]['media_consumo'])
        preco_gas = float(df_veic.iloc[0]['valor_litro_combustivel'])
    except:
        media = 30.0 
        preco_gas = 5.00

    # 2. Cálculos Financeiros
    custo_gasolina = (float(km_rodados) / media) * preco_gas if media > 0 else 0
    custo_depreciacao = float(km_rodados) * 0.10  # R$ 0,10 por km (Depreciação estimada)
    lucro_liquido = float(faturamento) - custo_gasolina - custo_depreciacao - float(gastos_extras)
    
    # 3. Salva no Banco (MySQL)
    query_insert = """
    INSERT INTO viagens (veiculo_id, data, km_rodados, faturamento, qtd_entregas, gastos_extras, descricao_extra, custo_gasolina_calc, custo_depreciacao_calc, lucro_liquido_calc)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    sucesso, msg = database.executar_query(query_insert, (veiculo_id, data, km_rodados, faturamento, qtd_entregas, gastos_extras, desc_extra, custo_gasolina, custo_depreciacao, lucro_liquido))
    
    if sucesso:
        # Chama a função do OUTRO arquivo para atualizar o odômetro da moto
        vehicle_controller.atualizar_km_veiculo(veiculo_id, km_rodados)
        return True, f"✅ Salvo! Lucro: R$ {lucro_liquido:.2f}"
    
    return False, msg

def listar_viagens(veiculo_id):
    # MySQL Query (Substitui o carregar_dados antigo)
    query = "SELECT * FROM viagens WHERE veiculo_id = %s ORDER BY data DESC"
    df = database.carregar_query(query, (veiculo_id,))
    
    if not df.empty:
        # Garante que os números venham como float e data como data
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