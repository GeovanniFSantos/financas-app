import pandas as pd
import os
import uuid

DB_FILE = 'financas_db.xlsx'

def gerar_id():
    return str(uuid.uuid4())[:8]

def inicializar_db():
    required_sheets = {
        'usuarios': ['username', 'nome', 'email', 'contato', 'senha'],
        'transacoes': ['id', 'username', 'data', 'tipo', 'categoria', 'valor', 'metodo_pagamento', 'descricao'],
        'veiculos': ['id', 'username', 'nome', 'tipo', 'placa', 'data_licenciamento', 'valor_licenciamento', 'km_atual', 'media_consumo', 'valor_litro_combustivel'],
        'manutencao': ['id', 'veiculo_id', 'item', 'km_intervalo', 'custo_estimado', 'km_ultima_troca', 'data_ultima_troca'],
        'viagens': ['id', 'veiculo_id', 'data', 'km_rodados', 'faturamento', 'qtd_entregas', 'gastos_extras', 'descricao_extra', 'custo_gasolina_calc', 'custo_depreciacao_calc', 'lucro_liquido_calc'],
        'contas_fixas': ['id', 'username', 'nome', 'valor_previsto', 'dia_vencimento', 'categoria'],
        
        # ATUALIZADO: Adicionei 'data_ultimo_rendimento'
        'metas': ['id', 'username', 'nome', 'valor_alvo', 'valor_guardado', 'data_limite', 'descricao', 'rendimento_mensal', 'data_ultimo_rendimento']
    }

    if not os.path.exists(DB_FILE):
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            for sheet, columns in required_sheets.items():
                pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet, index=False)
    else:
        try:
            xls = pd.ExcelFile(DB_FILE, engine='openpyxl')
            dict_dfs = {}
            for sheet in xls.sheet_names:
                dict_dfs[sheet] = pd.read_excel(xls, sheet)
            
            houve_mudanca = False
            for sheet, columns in required_sheets.items():
                if sheet not in dict_dfs:
                    dict_dfs[sheet] = pd.DataFrame(columns=columns)
                    houve_mudanca = True
                else:
                    for col in columns:
                        if col not in dict_dfs[sheet].columns:
                            # Preenche colunas novas
                            if 'data' in col:
                                dict_dfs[sheet][col] = pd.NaT
                            elif 'valor' in col or 'rendimento' in col:
                                dict_dfs[sheet][col] = 0.0
                            elif col == 'id':
                                dict_dfs[sheet]['id'] = [gerar_id() for _ in range(len(dict_dfs[sheet]))]
                            else:
                                dict_dfs[sheet][col] = ""
                            houve_mudanca = True
            
            if houve_mudanca:
                with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                    for sheet_name, df in dict_dfs.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            print(f"Erro DB: {e}")

# ... (MANTENHA AS OUTRAS FUNÇÕES IGUAIS: carregar_dados, salvar_no_excel, excluir, atualizar...)
def carregar_dados(sheet_name):
    inicializar_db()
    try:
        return pd.read_excel(DB_FILE, sheet_name=sheet_name, engine='openpyxl')
    except:
        return pd.DataFrame()

def salvar_no_excel(dataframe, sheet_name):
    try:
        xls = pd.ExcelFile(DB_FILE, engine='openpyxl')
        dict_dfs = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
        dict_dfs[sheet_name] = dataframe
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            for nome, df in dict_dfs.items():
                df.to_excel(writer, sheet_name=nome, index=False)
        return True, "Salvo com sucesso!"
    except PermissionError:
        return False, "⚠️ Feche o Excel!"
    except Exception as e:
        return False, f"Erro: {e}"

def excluir_registro(sheet_name, id_coluna, id_valor):
    df = carregar_dados(sheet_name)
    if df.empty: return False, "Tabela vazia"
    df_novo = df[df[id_coluna] != id_valor]
    return salvar_no_excel(df_novo, sheet_name)

def atualizar_registro(sheet_name, id_coluna, id_valor, novos_dados):
    df = carregar_dados(sheet_name)
    idx = df.index[df[id_coluna] == id_valor].tolist()
    if not idx: return False, "Registro não encontrado"
    for key, value in novos_dados.items():
        df.at[idx[0], key] = value
    return salvar_no_excel(df, sheet_name)

def buscar_usuario(username):
    df = carregar_dados('usuarios')
    if df.empty: return df
    user = df[df['username'] == username]
    if user.empty and 'email' in df.columns:
        user = df[df['email'] == username]
    return user