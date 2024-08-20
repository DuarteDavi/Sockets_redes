import sqlite3
import socket
import time
import random
import threading

HOST = 'localhost'  # Endereço IP do servidor
ports = [random.randint(1024, 4915) for _ in range(4)]  # Lista de portas aleatórias entre 1024 e 4915
PORT = random.choice(ports)  # Seleciona uma porta aleatória da lista
#PORT = 2620
print(f"Servidor iniciado em {HOST}:{PORT}")

# Conecta ao banco de dados SQLite
conn_db = sqlite3.connect('clientes.db', check_same_thread=False)  # check permite várias conexões no banco em threads diferentes
cursor = conn_db.cursor()

# Cria as tabelas 'clientes' e 'mensagens' se elas não existirem
cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (id TEXT, endereco TEXT, timestamp TEXT, PRIMARY KEY (id))''')
cursor.execute('''CREATE TABLE IF NOT EXISTS mensagens (cod_msg TEXT, dst TEXT, src TEXT, timestamp TEXT, msg_data TEXT, PRIMARY KEY (cod_msg, dst, src, timestamp))''')
cursor.execute('''CREATE TABLE IF NOT EXISTS grupos (group_id TEXT, timestamp TEXT, PRIMARY KEY (group_id))''')
cursor.execute('''CREATE TABLE IF NOT EXISTS grupo_clientes (group_id TEXT, cliente_id TEXT, FOREIGN KEY (group_id) REFERENCES grupos(group_id), FOREIGN KEY (cliente_id) REFERENCES clientes(id))''')
conn_db.commit()

# Dicionário global para armazenar as conexões dos clientes
client_connections = {}
client_connections_lock = threading.Lock()  # Lock para sincronizar o acesso ao dicionário

def handle_client(conn, addr):
    print(f"Conectado por {addr}")

    # Envia uma mensagem inicial para o cliente
    conn.sendall("Bem-vindo ao servidor. Envie '01' para se cadastrar. \n".encode())

    # Recebe dados do cliente
    data = conn.recv(1024).decode()
    print(f"Recebido do cliente: {data} \n")

    unique_id = None
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
                           (unique_id, addr[0], str(int(time.time()))))
            conn_db.commit()

    # Adicionar a conexão do cliente ao dicionário global
    if unique_id:
        with client_connections_lock:
            client_connections[unique_id] = conn
        print(f"Usuários conectados: {list(client_connections.keys())} \n")

        # Verificar se há mensagens pendentes para o cliente
        cursor.execute("SELECT cod_msg ,src, timestamp, msg_data FROM mensagens WHERE dst=?", (unique_id,))
        pending_messages = cursor.fetchall()
        for msg in pending_messages:
            cod_msg, src, timestamp, msg_data = msg
            conn.sendall(f"{cod_msg}{src}{unique_id}{timestamp}{msg_data}\n".encode())

        # Remover as mensagens pendentes entregues
        cursor.execute("DELETE FROM mensagens WHERE dst=?", (unique_id,))
        conn_db.commit()

    try:
        # Recebe dados do cliente
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                message = data.decode()
                print(f"Recebido de {unique_id}: {message} \n")

                if len(message) >= 256:
                    conn.sendall(f"Erro: Mensagem deve ter no máximo 256 caracteres! \n".encode())
                else:
                    cod = message[:2]
                    src = message[2:15].strip()  # Remove espaços extras
                    if cod == "03":
                        # cod(2)src(13)dst(13)timestamp(10)data(218)
                        dst = message[15:28].strip()
                        timestamp = message[28:38].strip()
                        msg_data = message[38:]
                    elif cod == "08":  # Confirmação de leitura
                        timestamp = message[15:25].strip()
                        msg_data = ""
                        dst = ""
                    elif cod == "10":  # Criação de grupo
                        # cod(2)criador(13)timestamp(10)members(7*13)
                        timestamp = message[15:25].strip()
                        members = message[25:].split()
                        members = ' '.join(members)
                        member_list = members.split(',')
                        # Add o src ao grupo
                        member_list.append(src)
                        dst = members
                        msg_data = ""

                    print(f"Mensagem decodificada - COD: {cod}, SRC: {src}, DST: '{dst}', TIMESTAMP: {timestamp}, DATA: {msg_data}")

                    if cod == "03":  # Mensagem de texto padrão
                        print('1')
                        is_group = False
                        cursor.execute("SELECT group_id FROM grupos WHERE group_id=?", (dst,))
                        result = cursor.fetchone()
                        if result:
                            is_group = True
                        # Confirmação que a mensagem é para um grupo
                        if is_group:
                            members = cursor.execute("SELECT cliente_id FROM grupo_clientes WHERE group_id=?", (dst,)).fetchall()
                            # Mandar mensagem para todos os membros do grupo
                            for user in members:
                                user_id = user[0]
                                with client_connections_lock:
                                    if user_id in client_connections:
                                        dest_conn = client_connections[user_id]
                                        dest_conn.sendall((data.decode() + "\n").encode())
                                        
                                        # Enviar confirmação de entrega ao membro do grupo
                                        delivery_confirmation = f"07{src}{timestamp}\n"
                                        conn.sendall(delivery_confirmation.encode())
                                        print(f"Confirmação de entrega enviada para {user_id}: {delivery_confirmation} \n")
                                    else:
                                        # Armazena a mensagem no banco de dados se o destinatário não estiver online
                                        cursor.execute("INSERT INTO mensagens (cod_msg ,dst, src, timestamp, msg_data) VALUES (?, ?, ?, ?, ?)",
                                                    (cod, user_id, src, timestamp, msg_data))
                                        conn_db.commit()
                                        conn.sendall(f"Erro: Destino {user_id} não encontrado. Mensagem armazenada para entrega futura. \n".encode())

                        else:
                            with client_connections_lock:
                                if dst in client_connections:
                                    dest_conn = client_connections[dst]
                                    dest_conn.sendall(data)

                                    # Enviar confirmação de entrega ao remetente
                                    delivery_confirmation = f"07{dst}{timestamp}\n"
                                    conn.sendall(delivery_confirmation.encode())
                                    print(f"Confirmação de entrega enviada para {src}: {delivery_confirmation} \n")

                                else:
                                    print('teste')
                                    # Armazena a mensagem no banco de dados se o destinatário não estiver online
                                    cursor.execute("INSERT INTO mensagens (cod_msg, dst, src, timestamp, msg_data) VALUES (?, ?, ?, ?, ?)",
                                                (cod, dst, src, timestamp, msg_data))
                                    conn_db.commit()
                                    conn.sendall(f"Erro: Destino {dst} não encontrado. Mensagem armazenada para entrega futura. \n".encode())

                    elif cod == "08":  # Confirmação de leitura
                        print(f"Confirmação de leitura recebida de {src} para mensagem enviada em {timestamp} \n")

                        # Notificar o cliente originador que sua menFsagem foi lida
                        notification_message = f"09{src}{timestamp}\n"
                        with client_connections_lock:
                            if src in client_connections:
                                origin_conn = client_connections[src]
                                origin_conn.sendall(notification_message.encode())
                                print(f"Notificação de leitura enviada para {src}: {notification_message} \n")
                            else:
                                print(f"Cliente originador {src} não está online. Não foi possível enviar a notificação de leitura. \n")
                    
                    elif cod == "10":  # Criação de grupo
                        group_id = ''.join([str(random.randint(0, 9)) for _ in range(13)])
                        print('member_list', member_list)
                        
                        # Inserir o grupo na tabela 'grupos'
                        cursor.execute("INSERT INTO grupos (group_id, timestamp) VALUES (?, ?)", (group_id, timestamp))
                        print('member_list', member_list)
                        for member in member_list:
                            if member == '':
                                continue
                            # Inserir os membros na tabela 'grupo_clientes'
                            cursor.execute("INSERT INTO grupo_clientes (group_id, cliente_id) VALUES (?, ?)", (group_id, member))
                        conn_db.commit()

                        # Envia a confirmação de criação do grupo para o cliente
                        # cod(2)criador(13)timestamp(10)members(7*13)
                        notification_message = f"11{group_id}{timestamp}{members}\n"
                        with client_connections_lock:
                            if member in client_connections:
                                dest_conn = client_connections[member]
                                dest_conn.sendall(notification_message.encode())
                                print(f"Grupo {group_id} criado com sucesso. \n")

            except ConnectionResetError:
                print(f"Conexão resetada pelo cliente {addr}.")
                break
    finally:
        # Remove a conexão do cliente do dicionário global
        with client_connections_lock:
            if unique_id in client_connections:
                del client_connections[unique_id]
        print(f"Conexão encerrada com {addr}. Usuário {unique_id} removido.")
        conn.close()

def start_server():#
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"Servidor ouvindo em {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_server()