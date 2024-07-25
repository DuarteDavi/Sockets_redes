import socket
import time

def start_client(server_host='10.229.21.163', server_port=48960):
    # Criar um socket TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Conectar ao servidor
    client_socket.connect((server_host, server_port))
    print(f"Conectado ao servidor em {server_host}:{server_port}")
    client_socket.settimeout(10.0)
    
    try:
        while True:
            
          
            recipient_id = input("Digite o ID do destinatário (13 dígitos): ")
            if len(recipient_id) != 13:
                print("O ID do destinatário deve ter exatamente 13 dígitos.")
                continue

            message_content = input("Digite o conteúdo da mensagem (máximo de 218 caracteres): ")
            if len(message_content) > 218:
                print("O conteúdo da mensagem deve ter no máximo 218 caracteres.")
                continue

            # Verifica se o usuário deseja sair antes de formatar e enviar a mensagem
            if recipient_id.lower() == 'sair' or message_content.lower() == 'sair':
                break

            timestamp = time.time()
            # Formatar a mensagem com '03', IP do cliente, ID do destinatário, timestamp e conteúdo da mensagem
            formatted_message = f'03{client_socket.getsockname()[0].replace(".", "")}{recipient_id}{int(timestamp)}{message_content.replace(" ", "_")}'
            client_socket.sendall(formatted_message.encode())
            print("Mensagem enviada ao servidor:", formatted_message)
            continue
            # Receber a resposta do servidor
            data = client_socket.recv(1024)
            
            
            
    finally:
        # Fecha o socket independentemente de como o loop while termina
        client_socket.close()
        

if __name__ == '__main__':
    start_client(server_host='10.229.21.163', server_port=48960)