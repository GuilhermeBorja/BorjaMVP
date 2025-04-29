import sqlite3

DATABASE = 'app.db'

def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection(); cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nivel INTEGER
        )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_processo TEXT,
            etapas_quantidade INTEGER,
            responsavel_geral TEXT,
            data_criacao TEXT,
            data_termino_ideal TEXT,
            tempo_total TEXT,
            status TEXT
        )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS etapas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo_id INTEGER,
            nome_etapa TEXT,
            responsavel_etapa TEXT,
            tempo_gasto TEXT,
            data_termino_real TEXT,
            FOREIGN KEY(processo_id) REFERENCES processos(id)
        )''')
    conn.commit()
    cur.execute("INSERT OR IGNORE INTO users (username, password, nivel) VALUES (?,?,?)", ("admin","admin",10))
    conn.commit(); conn.close()

if __name__ == "__main__":
    create_tables()
    print("Banco inicializado e usuário admin garantido.")
