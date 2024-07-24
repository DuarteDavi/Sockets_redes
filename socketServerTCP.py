import sqlite3
import socket
import time
import random

HOST = '0.0.0.0'
ports = [random.randint(1024, 49151) for _ in range(4)]  # Lista de portas aleatórias entre 1024 e 49151
PORT = random.choice(ports)  # Seleciona uma porta aleatória da lista

print(f"Servidor iniciado em {HOST}:{PORT}")

# Conecta ao banco de dados SQLite
conn_db = sqlite3.connect('clientes.db')
cursor = conn_db.cursor()

# Cria a tabela 'clientes' se ela não existir
cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (id TEXT, endereco TEXT, timestamp TEXT)''')
# Cria a tabela 'mensagens_pendentes' se ela não existir
cursor.execute('''CREATE TABLE IF NOT EXISTS mensagens_pendentes (src TEXT, dst TEXT, timestamp TEXT, data TEXT)''')

def enviar_mensagens_pendentes(dst, conn):
    cursor.execute("SELECT src, timestamp, data FROM mensagens_pendentes WHERE dst=?", (dst,))
    mensagens = cursor.fetchall()
    for msg in mensagens:
        src, timestamp, data = msg
        mensagem_formatada = f"Mensagem de: {src}, Horário: {timestamp}, Conteúdo: {data}"
        conn.sendall(mensagem_formatada.encode())
    cursor.execute("DELETE FROM mensagens_pendentes WHERE dst=?", (dst,))
    conn_db.commit()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    clientes_conectados = {}  # Dicionário para manter o controle dos clientes conectados
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
                    clientes_conectados[unique_id] = conn  # Adiciona o cliente ao dicionário de clientes conectados
                    enviar_mensagens_pendentes(unique_id, conn)  # Envia mensagens pendentes, se houver
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
                    posix_time = time.time()
                    cursor.execute("INSERT INTO clientes (id, endereco, timestamp) VALUES (?, ?, ?)",
                                   (unique_id, addr[0], str(posix_time)))
                    conn_db.commit()
                    clientes_conectados[unique_id] = conn  # Adiciona o cliente ao dicionário de clientes conectados

                # Dentro do loop para tratamento de mensagens do cliente
                while True:
                    data = conn.recv(1024)
                    if not data:
                        del clientes_conectados[unique_id]  # Remove o cliente do dicionário de clientes conectados
                        break  # Trata desconexão do cliente

                    # Extrai destinatário_id e mensagem da string recebida
                    try:
                        destinatario_id, mensagem = data.decode().split(':', 1)
                    except ValueError:
                        # Formato inválido, não processa a mensagem
                        print("Formato de mensagem inválido.")
                        continue

                    # Verifica se o destinatário está conectado
                    if destinatario_id in clientes_conectados:
                        # Envia a mensagem ao destinatário
                        try:
                            clientes_conectados[destinatario_id].sendall(mensagem.encode())
                        except Exception as e:
                            print(f"Erro ao enviar mensagem para {destinatario_id}: {e}")
                    else:
                        # Armazena a mensagem na base de dados para destinatários desconectados
                        posix_time = time.time()
                        cursor.execute("INSERT INTO mensagens_pendentes (src, dst, timestamp, data) VALUES (?, ?, ?, ?)",
                                    (unique_id, destinatario_id, str(posix_time), mensagem))
                        conn_db.commit()

        except ConnectionResetError:
            print(f"Conexão perdida com {addr}.")
        except Exception as e:
            print(f"Erro inesperado: {e}")