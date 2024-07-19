import socket
import time

HOST = "10.228.247.235"  # Endereço de interface de loopback padrão (localhost)
PORT = 1025  # Porta para escutar (portas não privilegiadas são > 1023)
posix_time = time.time() # Solicita a hora POSIX

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))  # Associa o socket ao endereço e porta especificados
    s.listen()  # Coloca o socket em modo de escuta
    conn, addr = s.accept()  # Aceita uma conexão de cliente
    with conn:
        print(f"Conectado por {addr}")  # Imprime o endereço do cliente conectado
        while True:
            data = conn.recv(1024)  # Recebe dados do cliente
            print(f"Recebido de {addr[0]}: {data.decode()} em hora POSIX: {posix_time}")  # O ip do usuário conectado e a mensagem enviada com horário POSIX
            # Verifica se a mensagem do cliente é maior que 218 caracteres
            if len(data.decode()) > 218:
                # Envia uma mensagem de erro ao cliente
                conn.sendall(f"Erro: Mensagem muito grande! (Máximo de 218 caracteres)".encode())
                data = conn.recv(1024)
            else:
                # Envia uma mensagem de sucesso ao cliente
                conn.sendall(f"Sucesso: Mensagem recebida com sucesso!".encode() + b" em hora POSIX: " + str(posix_time).encode())
                data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)  # Envia de volta os dados recebidos para o cliente
