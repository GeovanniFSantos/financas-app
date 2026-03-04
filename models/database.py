import mysql.connector
import pandas as pd
import streamlit as st

def get_connection():
    """Conecta ao MySQL usando as credenciais do secrets.toml"""
    try:
        # Tenta pegar dos secrets (funciona local e no deploy)
        db_config = st.secrets["mysql"]
        
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            port=db_config.get("port", 3306)
        )
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar no MySQL: {e}")
        return None

def executar_query(query, valores=None):
    """Executa INSERT, UPDATE, DELETE"""
    conn = get_connection()
    if not conn: return False, "Sem conexão"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, valores)
        conn.commit()
        return True, "Sucesso"
    except Exception as e:
        return False, str(e)
    finally:
        if conn: conn.close()

def carregar_query(query, valores=None):
    """Executa SELECT e retorna um DataFrame do Pandas"""
    conn = get_connection()
    if not conn: return pd.DataFrame()
    
    try:
        # O Pandas já lê direto do banco!
        df = pd.read_sql(query, conn, params=valores)
        return df
    except Exception as e:
        st.error(f"Erro SQL: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

# --- FUNÇÕES ESPECÍFICAS (MANTENDO A COMPATIBILIDADE) ---

def buscar_usuario(username_ou_email):
    query = "SELECT * FROM usuarios WHERE username = %s OR email = %s"
    return carregar_query(query, (username_ou_email, username_ou_email))

def buscar_usuario_por_id(user_id):
    query = "SELECT * FROM usuarios WHERE id = %s"
    return carregar_query(query, (user_id,))

# --- FUNÇÃO AUXILIAR PARA PEGAR ID PELO NOME ---
def get_user_id(username):
    df = buscar_usuario(username)
    if not df.empty:
        return int(df.iloc[0]['id'])
    return None

def salvar_no_excel(dataframe, sheet_name):
    """
    OBSOLETO: Esta função existia no Excel. 
    Agora usamos INSERTs diretos no controller.
    Mantida vazia apenas para não quebrar imports antigos se houver.
    """
    pass