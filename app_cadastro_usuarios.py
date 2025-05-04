import streamlit as st
import sqlite3
from db_connect import get_connection
import hashlib

def hash_password(password):
    """Função para criar hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_admin_access():
    """Verifica se o usuário atual tem nível 10 (admin)"""
    if 'user' not in st.session_state:
        return False
    return st.session_state.user.get('nivel') == 10

def get_access_levels():
    """Retorna a lista de níveis de acesso disponíveis"""
    return {
        1: "Visualizar e editar apenas dados criados por você",
        2: "Apenas visualizar todos os dados do seu estado",
        3: "Visualizar e editar todos os dados do seu estado",
        4: "Apenas visualizar todos os dados do seu setor",
        5: "Visualizar e editar todos os dados do seu setor",
        6: "Apenas visualizar todos os dados da sua empresa",
        7: "Visualizar e editar todos os dados da sua empresa",
        8: "Visualizar todos os dados",
        9: "Visualizar e editar todos os dados",
        10: "Visualizar, editar e remover todos os dados, criar e apagar usuários"
    }

def cadastro_usuarios():
    if not check_admin_access():
        st.error("Acesso negado. Apenas administradores podem acessar esta página.")
        return

    st.title("Cadastro de Usuários")
    
    # Formulário de cadastro
    with st.form("form_cadastro_usuario"):
        username = st.text_input("Login")
        password = st.text_input("Senha", type="password")
        estado = st.text_input("Estado")
        empresa = st.text_input("Empresa")
        setor = st.text_input("Setor")
        email = st.text_input("E-mail")
        nome_amigavel = st.text_input("Nome amigável")
        
        # Seleção de nível de acesso
        st.subheader("Nível de Acesso")
        access_levels = get_access_levels()
        nivel_acesso = st.selectbox(
            "Selecione o nível de acesso",
            options=list(access_levels.keys()),
            format_func=lambda x: f"{x} - {access_levels[x]}"
        )
        
        submitted = st.form_submit_button("Cadastrar Usuário")
        
        if submitted:
            if not all([username, password, estado, empresa, setor, email, nome_amigavel]):
                st.error("Todos os campos são obrigatórios!")
                return
            
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Verifica se o usuário já existe
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    st.error("Este login já está em uso!")
                    return
                
                # Insere o novo usuário
                hashed_password = hash_password(password)
                cursor.execute("""
                    INSERT INTO users (username, password, nivel, estado, empresa, setor, email, nome_amigavel)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, hashed_password, nivel_acesso, estado, empresa, setor, email, nome_amigavel))
                
                conn.commit()
                conn.close()
                st.success("Usuário cadastrado com sucesso!")
                st.session_state.pagina = "visualizar"
                st.rerun()
                
            except sqlite3.Error as e:
                st.error(f"Erro ao cadastrar usuário: {str(e)}")

    # Lista de usuários existentes
    st.subheader("Usuários Cadastrados")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, nivel, estado, empresa, setor, email, nome_amigavel FROM users")
        users = cursor.fetchall()
        
        if users:
            for user in users:
                with st.expander(f"Usuário: {user['username']}"):
                    st.write(f"Nível de Acesso: {user['nivel']} - {access_levels[user['nivel']]}")
                    st.write(f"Estado: {user['estado']}")
                    st.write(f"Empresa: {user['empresa']}")
                    st.write(f"Setor: {user['setor']}")
                    st.write(f"E-mail: {user['email']}")
                    st.write(f"Nome Amigável: {user['nome_amigavel']}")
                    
                    if st.button(f"Excluir {user['username']}", key=f"delete_{user['username']}"):
                        cursor.execute("DELETE FROM users WHERE username = ?", (user['username'],))
                        conn.commit()
                        st.success(f"Usuário {user['username']} excluído com sucesso!")
                        st.experimental_rerun()
        else:
            st.info("Nenhum usuário cadastrado.")
            
    except sqlite3.Error as e:
        st.error(f"Erro ao listar usuários: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    cadastro_usuarios() 