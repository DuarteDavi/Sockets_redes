import socket
import time

def start_client(server_host='10.228.247.158', server_port=1620):
    # Criar um socket TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Definir timeout
    client_socket.settimeout(30.0)  # Aumentar o timeout para 30 segundos

    try:
        # Conectar ao servidor
        client_socket.connect((server_host, server_port))
        print(f"Conectado ao servidor em {server_host}:{server_port}")

        # Receber mensagem inicial do servidor
        data = client_socket.recv(1024).decode()
        print(f"Mensagem do servidor: {data}")

        while True:
            message = "01"
            client_socket.sendall(message.encode())
            print("Mensagem '01' enviada.")

            recipient_id = input("Digite o ID do destinatário (15 dígitos): ")
            if len(recipient_id) != 15:
                print("O ID do destinatário deve ter exatamente 15 dígitos.")
                continue

            message_content = input("Digite o conteúdo da mensagem (máximo de 218 caracteres): ")
            if len(message_content) > 218:
                print("O conteúdo da mensagem deve ter no máximo 218 caracteres.")
                continue

            timestamp = time.time()
            # Formatar a mensagem com '03', IP do cliente, ID do destinatário, timestamp e conteúdo da mensagem
            formatted_message = f'03{client_socket.getsockname()[0].replace(".", "")}{recipient_id}{int(timestamp)}{message_content.replace(" ", "_")}'
            client_socket.sendall(formatted_message.encode())
            print("Mensagem enviada ao servidor:", formatted_message)
            
            # Receber a resposta do servidor
            try:
                data = client_socket.recv(1024).decode()
                print(f"Resposta do servidor: {data}")
            except socket.timeout:
                print("Tempo de espera excedido. Nenhuma resposta recebida do servidor.")

    finally:
        # Fecha o socket independentemente de como o loop while termina
        client_socket.close()

if __name__ == '__main__':
    start_client(server_host='10.228.247.158', server_port=1620)
