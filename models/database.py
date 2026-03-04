import mysql.connector
import pandas as pd
import streamlit as st

# Função para conectar (sem cache, pois a conexão expira rápido)
def get_connection():
    try:
        # Tenta pegar dos secrets (Streamlit Cloud ou local)
        # Se der erro de chave, verifique se o arquivo .streamlit/secrets.toml existe
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

# --- CACHE DE DADOS (VELOCIDADE) ---
# ttl=300 significa: "Lembre disso por 5 minutos"
@st.cache_data(ttl=300, show_spinner=False)
def carregar_query(query, valores=None):
    """Executa SELECT e retorna um DataFrame (COM CACHE)"""
    conn = get_connection()
    if not conn: return pd.DataFrame()
    
    try:
        # Se valores for uma lista, converte para tupla (o cache precisa disso)
        if isinstance(valores, list):
            valores = tuple(valores)
            
        df = pd.read_sql(query, conn, params=valores)
        return df
    except Exception as e:
        print(f"Erro SQL Consultar: {e}") 
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def executar_query(query, valores=None):
    """Executa INSERT, UPDATE, DELETE e LIMPA O CACHE"""
    conn = get_connection()
    if not conn: return False, "Sem conexão"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, valores)
        conn.commit()
        
        # --- LIMPEZA DE CACHE ---
        # Se salvamos algo novo, limpamos a memória para o usuário ver o dado atualizado
        st.cache_data.clear()
        
        return True, "Sucesso"
    except Exception as e:
        print(f"Erro SQL Executar: {e}")
        return False, str(e)
    finally:
        if conn: conn.close()

# --- FUNÇÕES AUXILIARES ---

def buscar_usuario(username_ou_email):
    query = "SELECT * FROM usuarios WHERE username = %s OR email = %s"
    return carregar_query(query, (username_ou_email, username_ou_email))

def get_user_id(username):
    df = buscar_usuario(username)
    if not df.empty:
        return int(df.iloc[0]['id'])
    return None