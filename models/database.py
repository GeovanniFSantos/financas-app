import pandas as pd
import os
import uuid

DB_FILE = 'financas_db.xlsx'

# Definição das colunas obrigatórias
REQUIRED_SHEETS = {
    'usuarios': ['username', 'nome', 'email', 'contato', 'senha', 'foto_perfil'],
    'transacoes': ['id', 'username', 'data', 'tipo', 'categoria', 'valor', 'metodo_pagamento', 'descricao'],
    'veiculos': ['id', 'username', 'nome', 'tipo', 'placa', 'data_licenciamento', 'valor_licenciamento', 'km_atual', 'media_consumo', 'valor_litro_combustivel'],
    'manutencao': ['id', 'veiculo_id', 'item', 'km_intervalo', 'custo_estimado', 'km_ultima_troca', 'data_ultima_troca'],
    'viagens': ['id', 'veiculo_id', 'data', 'km_rodados', 'faturamento', 'qtd_entregas', 'gastos_extras', 'descricao_extra', 'custo_gasolina_calc', 'custo_depreciacao_calc', 'lucro_liquido_calc'],
    'contas_fixas': ['id', 'username', 'nome', 'valor_previsto', 'dia_vencimento', 'categoria'],
    'metas': ['id', 'username', 'nome', 'valor_alvo', 'valor_guardado', 'data_limite', 'descricao', 'rendimento_mensal', 'data_ultimo_rendimento']
}

def gerar_id():
    return str(uuid.uuid4())[:8]

def inicializar_db():
    if not os.path.exists(DB_FILE):
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            for sheet, columns in REQUIRED_SHEETS.items():
                pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet, index=False)
    else:
        # Verifica se todas as abas existem e têm as colunas certas
        try:
            xls = pd.ExcelFile(DB_FILE, engine='openpyxl')
            dict_dfs = {}
            houve_mudanca = False
            
            for sheet in xls.sheet_names:
                dict_dfs[sheet] = pd.read_excel(xls, sheet)
            
            for sheet, columns in REQUIRED_SHEETS.items():
                if sheet not in dict_dfs:
                    dict_dfs[sheet] = pd.DataFrame(columns=columns)
                    houve_mudanca = True
                else:
                    # Se a aba existe mas está sem colunas (vazia), recria o cabeçalho
                    if dict_dfs[sheet].empty and len(dict_dfs[sheet].columns) == 0:
                         dict_dfs[sheet] = pd.DataFrame(columns=columns)
                         houve_mudanca = True
                    else:
                        # Garante que todas as colunas necessárias existam
                        for col in columns:
                            if col not in dict_dfs[sheet].columns:
                                if 'data' in col: dict_dfs[sheet][col] = pd.NaT
                                elif 'valor' in col or 'rendimento' in col: dict_dfs[sheet][col] = 0.0
                                elif col == 'id': dict_dfs[sheet]['id'] = [gerar_id() for _ in range(len(dict_dfs[sheet]))]
                                else: dict_dfs[sheet][col] = ""
                                houve_mudanca = True
            
            if houve_mudanca:
                with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                    for sheet_name, df in dict_dfs.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            print(f"Erro ao inicializar DB: {e}")

def carregar_dados(sheet_name):
    inicializar_db()
    try:
        df = pd.read_excel(DB_FILE, sheet_name=sheet_name, engine='openpyxl')
        
        # --- A CORREÇÃO DO KEYERROR ESTÁ AQUI ---
        # Se a tabela vier sem as colunas certas, retornamos um DataFrame vazio COM AS COLUNAS CERTAS
        required_cols = REQUIRED_SHEETS.get(sheet_name, [])
        
        # Verifica se faltam colunas essenciais (como 'username')
        if not df.empty and required_cols:
             missing = [c for c in required_cols if c not in df.columns]
             if missing:
                 # Se faltar coluna, retorna vazio mas estruturado para não quebrar
                 return pd.DataFrame(columns=required_cols)
        
        # Se estiver vazia, garante que tem o cabeçalho
        if df.empty:
            return pd.DataFrame(columns=required_cols)
            
        return df
    except:
        return pd.DataFrame(columns=REQUIRED_SHEETS.get(sheet_name, []))

def salvar_no_excel(dataframe, sheet_name):
    try:
        # Garante que o arquivo existe antes de ler
        if not os.path.exists(DB_FILE): inicializar_db()
            
        xls = pd.ExcelFile(DB_FILE, engine='openpyxl')
        dict_dfs = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
        dict_dfs[sheet_name] = dataframe
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            for nome, df in dict_dfs.items():
                df.to_excel(writer, sheet_name=nome, index=False)
        return True, "Salvo com sucesso!"
    except PermissionError:
        return False, "⚠️ Feche o arquivo Excel aberto no seu PC!"
    except Exception as e:
        return False, f"Erro: {e}"

# Funções auxiliares
def excluir_registro(sheet_name, id_coluna, id_valor):
    df = carregar_dados(sheet_name)
    if df.empty: return False, "Tabela vazia"
    df[id_coluna] = df[id_coluna].astype(str)
    df_novo = df[df[id_coluna] != str(id_valor)]
    return salvar_no_excel(df_novo, sheet_name)

def atualizar_registro(sheet_name, id_coluna, id_valor, novos_dados):
    df = carregar_dados(sheet_name)
    df[id_coluna] = df[id_coluna].astype(str)
    idx = df.index[df[id_coluna] == str(id_valor)].tolist()
    if not idx: return False, "Registro não encontrado"
    for key, value in novos_dados.items():
        df.at[idx[0], key] = value
    return salvar_no_excel(df, sheet_name)

def buscar_usuario(username_ou_email):
    # Garante que carrega com as colunas certas
    df = carregar_dados('usuarios')
    if df.empty: return pd.DataFrame()
    
    # 1. Tenta Username
    user = df[df['username'] == username_ou_email]
    
    # 2. Se não achou, Tenta Email (se a coluna existir)
    if user.empty and 'email' in df.columns:
        user = df[df['email'] == username_ou_email]
        
    return user