import sqlite3
import hashlib

DATABASE = 'app.db'

def hash_password(password):
    """Função para criar hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de usuários para login e hierarquia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nivel INTEGER NOT NULL,
            estado TEXT NOT NULL,
            empresa TEXT NOT NULL,
            setor TEXT NOT NULL,
            email TEXT NOT NULL,
            nome_amigavel TEXT NOT NULL
        )
    ''')

    # Tabela de processos – inclui data_termino_real para atualização posterior
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_processo TEXT NOT NULL,
            etapas_quantidade INTEGER,
            responsavel_geral TEXT,
            data_criacao TEXT,
            data_termino_ideal TEXT,
            data_termino_real TEXT,
            tempo_total REAL,
            status TEXT
        )
    ''')

    # Tabela de etapas – inclui data_termino_real para cada etapa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etapas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo_id INTEGER,
            nome_etapa TEXT,
            responsavel_etapa TEXT,
            tempo_gasto REAL,
            data_termino_real TEXT,
            FOREIGN KEY (processo_id) REFERENCES processos(id)
        )
    ''')

    conn.commit()

    # Insere o usuário admin de forma definitiva com senha com hash
    hashed_admin_password = hash_password("admin")
    cursor.execute("""
        INSERT OR IGNORE INTO users 
        (username, password, nivel, estado, empresa, setor, email, nome_amigavel) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("admin", hashed_admin_password, 10, "SP", "Admin", "TI", "admin@admin.com", "Administrador"))
    conn.commit()

    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tabelas criadas com sucesso e usuário admin inserido permanentemente!")
