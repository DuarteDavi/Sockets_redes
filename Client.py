import socket

def start_client(server_host='10.229.21.163', server_port=17574):
    # Criar um socket TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Conectar ao servidor
    client_socket.connect((server_host, server_port))
    print(f"Conectado ao servidor em {server_host}:{server_port}")
    client_socket.settimeout(10.0) 
    
    while True:
       
        message = input("Digite a sua mensagem (Digite 'sair' para sair): ")  # Enviar uma mensagem
        if message.lower() == 'sair' :
            break
        client_socket.sendall(message.encode())

        # Receber a resposta do servidor
        data = client_socket.recv(1024)
        print("Recebido do servidor:", data.decode())

    # Fecha o socket
    client_socket.close()



if __name__ == '__main__':
    start_client(server_host='10.229.21.163', server_port=17574)

