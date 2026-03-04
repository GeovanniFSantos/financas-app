from models import database
import pandas as pd

def listar_todos_usuarios():

    query = """
        SELECT id, username, email, nivel_acesso, status_conta, data_expiracao 
        FROM usuarios 
        WHERE username NOT IN ('solucaosobmedida')
    """
    return database.carregar_query(query)

def alterar_status_usuario(user_id, novo_status):
    """Ativa ou Suspende um usuário"""
    query = "UPDATE usuarios SET status_conta = %s WHERE id = %s"
    return database.executar_query(query, (novo_status, user_id))

def definir_validade(user_id, data):
    """Define até quando o acesso é válido (para mensalidades)"""
    query = "UPDATE usuarios SET data_expiracao = %s WHERE id = %s"
    return database.executar_query(query, (data, user_id))

