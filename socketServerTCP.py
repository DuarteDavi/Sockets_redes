import sqlite3
import socket
import time
import random

HOST = '0.0.0.0'
ports = [random.randint(1024, 4915) for _ in range(4)]  # Lista de portas aleatórias entre 1024 e 4915
PORT = random.choice(ports)  # Seleciona uma porta aleatória da lista
print(f"Servidor iniciado em {HOST}:{PORT}")

# Conecta ao banco de dados SQLite
conn_db = sqlite3.connect('clientes.db')
cursor = conn_db.cursor()

# Cria a tabela 'clientes' se ela não existir
cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (id TEXT, endereco TEXT, timestamp TEXT)''')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Aguardando conexões na porta {PORT}...")
    while True:
        try:
            conn, addr = s.accept()
            with conn:
                print(f"Conectado por {addr}")

                # Envia uma mensagem inicial para o cliente
                conn.sendall("Bem-vindo ao servidor. Envie '01' para se cadastrar. \n".encode())

                # Recebe dados do cliente
                data = conn.recv(1024).decode()
                print(f"Recebido do cliente: {data} \n")

                if data == '01':
                    # Verifica se já existe um ID associado a este IP
                    cursor.execute("SELECT id FROM clientes WHERE endereco=?", (addr[0],))
                    existing_id = cursor.fetchone()

                    if existing_id:
                        unique_id = existing_id[0]
                        print(f"Conectado por {addr} com ID {unique_id} \n")
                        conn.sendall(f"02{unique_id} \n".encode())
                    else:
                        # Se não existe ID, cria um novo ID
                        unique_id = ''.join([str(random.randint(0, 9)) for _ in range(13)])
                        conn.sendall(f"02{unique_id} \n".encode())
                        
                        # Insere o ID único e o endereço do cliente no banco de dados
                        cursor.execute("INSERT INTO clientes (id, endereco, timestamp) VALUES (?, ?, ?)",
                                       (unique_id, addr[0], str(time.time())))
                        conn_db.commit()

                else:
                    conn.sendall("Mensagem inválida. Envie '01' para se cadastrar. \n".encode())

                # Recebe dados do cliente
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break

                    posix_time = time.time()
                    print(f"Recebido de {addr[0]}: {data.decode()} \n")
                    if len(data.decode()) > 218:
                        conn.sendall(f"Erro: Mensagem muito grande! (Máximo de 218 caracteres) \n".encode())
                    else:
                        conn.sendall(f"Sucesso: Mensagem recebida com sucesso! \n".encode())

        except ConnectionResetError:
            print(f"Conexão perdida com {addr}.")
        except Exception as e:
            print(f"Erro inesperado: {e}")
