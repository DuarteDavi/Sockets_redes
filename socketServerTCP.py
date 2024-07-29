import sqlite3
import socket
import time
import random

HOST = '0.0.0.0'
ports = [random.randint(1024, 4915) for _ in range(4)]  # Lista de portas aleatórias entre 1024 e 4915
PORT = random.choice(ports)  # Seleciona uma porta aleatória da lista
posix_time = time.time()
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
                conn.sendall("Bem-vindo ao servidor. Envie '01' para se cadastrar.".encode())

                # Recebe dados do cliente
                data = conn.recv(1024)
                if not data:
                    continue

                # Verifica se já existe um ID associado a este IP
                cursor.execute("SELECT id FROM clientes WHERE endereco=?", (addr[0],))
                existing_id = cursor.fetchone()

                if existing_id:
                    unique_id = existing_id[0]
                    print(f"Conectado por {addr} com ID {unique_id}")
                else:
                    # Se não existe ID, envia mensagem para se cadastrar
                    conn.sendall("Parece que você não está cadastrado em nosso servidor, envie '01' para se cadastrar.".encode())
                    print(f"Enviado pedido de cadastro para {addr}")
                    data = conn.recv(1024)
                    if not data:
                        continue

                    while data.decode() != '01':
                        print(f"Received invalid message from {addr}, not in database.")
                        conn.sendall("Parece que você não está cadastrado em nosso servidor, envie '01' para se cadastrar.".encode())
                        data = conn.recv(1024)
                        if not data:
                            continue
                    unique_id = '02' + ''.join([str(random.randint(0, 9)) for _ in range(13)])
                    conn.sendall(f"Seu ID único é: {unique_id}".encode())
                    
                    # Insere o ID único e o endereço do cliente no banco de dados
                    cursor.execute("INSERT INTO clientes (id, endereco, timestamp) VALUES (?, ?, ?)",
                                   (unique_id, addr[0], str(posix_time)))
                    conn_db.commit()

                # Recebe dados do cliente
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break

                    posix_time = time.time()
                    print(f"Recebido de {addr[0]}: {data.decode()} em hora POSIX: {posix_time}")
                    if len(data.decode()) > 218:
                        conn.sendall(f"Erro: Mensagem muito grande! (Máximo de 218 caracteres)".encode())
                    else:
                        conn.sendall(f"Sucesso: Mensagem recebida com sucesso! em hora POSIX: {posix_time}".encode())

        except ConnectionResetError:
            print(f"Conexão perdida com {addr}.")
        except Exception as e:
            print(f"Erro inesperado: {e}")
