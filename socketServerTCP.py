import sqlite3
import socket
import time
import random

HOST = '0.0.0.0'
ports = [random.randint(1024, 49151) for _ in range(4)]  # Lista de portas aleatórias entre 1024 e 49151
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
    while True:
        try:
            conn, addr = s.accept()
            with conn:
                print(f"Conectado por {addr}")

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
                    data = conn.recv(1024)

                    while data.decode() != '01':
                        print(f"Received invalid message from {addr}")
                        conn.sendall("Parece que você não está cadastrado em nosso servidor, envie '01' para se cadastrar.".encode())
                        data = conn.recv(1024)

                    # Se chegou aqui, significa que data.decode() é '01'
                    unique_id = '02' + ''.join([str(random.randint(0, 9)) for _ in range(13)])
                    conn.sendall(f"Seu ID único é: {unique_id}".encode())

                    # Insere o ID único e o endereço do cliente no banco de dados
                    cursor.execute("INSERT INTO clientes (id, endereco, timestamp) VALUES (?, ?, ?)",
                                   (unique_id, addr[0], str(posix_time)))
                    conn_db.commit()

                # Loop para tratamento de mensagens do cliente
                while True:
                    posix_time = time.time()
                    print(f"Recebido de {addr[0]}: {data.decode()} em hora POSIX: {posix_time}")
                    if len(data.decode()) > 218:
                        # Envia uma mensagem de erro ao cliente
                        conn.sendall(f"Erro: Mensagem muito grande! (Máximo de 218 caracteres)".encode())
                    else:
                        # Envia uma mensagem de sucesso ao cliente
                        conn.sendall(f"Sucesso: Mensagem recebida com sucesso! em hora POSIX: {posix_time}".encode())

                    data = conn.recv(1024)
                    if not data:
                        break  # Trata desconexão do cliente

        except ConnectionResetError:
            print(f"Conexão perdida com {addr}.")
        except Exception as e:
            print(f"Erro inesperado: {e}")