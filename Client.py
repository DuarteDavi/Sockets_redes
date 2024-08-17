import socket
import time
import datetime

class Client:
    def __init__(self, host, port):
        self.port = port
        self.host = host
        
        try:
            # Criar um socket TCP
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Definir timeout
            self.client_socket.settimeout(10.0)  # Timeout de 10 segundos

            # Dicionário para armazenar mensagens trocadas entre IDs
            self.messages_dict = {}
            
            # Armazena confirmações de entrega
            self.delivery_confirmations = {} 
            
            self.start()
        except Exception as e:
            print(f"Erro ao criar o socket: {e}")
            
        
    def __convert_timestamp(timestamp):
            # Converter o timestamp Unix para um objeto datetime
            dt_object = datetime.datetime.fromtimestamp(timestamp)
            
            # Formatar o objeto datetime para uma string legível
            human_readable_time = dt_object.strftime('%H:%M:%S em %d/%m/%Y')
            
            return human_readable_time

    def __display_messages_with_id(participant_id):
            if participant_id in messages_dict:
                print(f"Mensagens trocadas com {participant_id}:")
                for msg in messages_dict[participant_id]:
                    print(msg)
            else:
                print(f"Nenhuma mensagem trocada com o ID {participant_id}.\n")
                
    def choices(self):
        print("--------------------")
        print("Menu:")
        print("1. Enviar mensagem")
        print("2. Verificar mensagens recebidas")
        print("3. Grupos")
        print("9. Encerrar o programa")
        print("--------------------")
        
        choice = input("Escolha uma opção: ")
        return choice
    
    def send_message(self, recipient_id, message_content):
        timestamp = int(time.time())
        # Formatar a mensagem com '03', o ID do cliente, ID do destinatário, timestamp e conteúdo da mensagem
        formatted_message = f'03{unique_id}{recipient_id}{str(timestamp).ljust(10)}{message_content.replace(" ", "_")}'
        self.client_socket.sendall(formatted_message.encode())
        print("Mensagem enviada ao servidor: ", formatted_message + "\n")

        # Armazenar a mensagem enviada
        if recipient_id not in messages_dict:
            messages_dict[recipient_id] = []
        messages_dict[recipient_id].append(f"Enviado para {recipient_id} em {convert_timestamp(timestamp)}: {message_content}")
    
    def verify_messages(self):
        try:
            data = self.client_socket.recv(1024).decode()
            if data:
                if data.startswith("Sucesso") or data.startswith("Erro"):
                    print(f"Resposta do servidor: {data} \n")
                # Processar confirmação de entrega    
                elif data.startswith("07"):
                    cod = data[:2]
                    dst = data[2:15]
                    timestamp_str = data[15:25].strip()

                    try:
                        timestamp = int(timestamp_str)
                        print(f"Confirmação de entrega: Mensagens enviadas para {dst} até {convert_timestamp(timestamp)} foram entregues.")

                        # Atualizar mensagens enviadas para o destinatário
                        if dst in messages_dict:
                            messages_dict[dst] = [msg for msg in messages_dict[dst] if int(msg.split(' em ')[1].split(': ')[0]) <= timestamp]
                    except ValueError:
                        print(f"Erro ao converter o timestamp: {timestamp_str} \n")
                else:
                    # Processar mensagem recebida (resposta do servidor com dados de quem enviou e data)
                    src_id = data[2:15].strip()  # ID do remetente
                    timestamp_str = data[30:40].strip()  # Timestamp
                    message_data = data[40:].strip().replace("_", " ")  # Conteúdo da mensagem

                    try:
                        timestamp = int(timestamp_str)
                        print(f"Mensagem recebida de {src_id} em {convert_timestamp(timestamp)}: {message_data} \n")

                        # Armazenar a mensagem recebida
                        if src_id not in messages_dict:
                            messages_dict[src_id] = []
                        messages_dict[src_id].append(f"Recebido de {src_id} em {convert_timestamp(timestamp)}: {message_data}")
                    except ValueError:
                        print(f"Erro ao converter o timestamp: {timestamp_str} \n")
            else:
                print("Nenhuma mensagem recebida. \n")
        except socket.timeout:
            print("Nenhuma mensagem recebida. \n")

    def chosen_choice(self):
        while True:
            choice = self.choices()
            if choice == '1':
                # Enviar mensagem ao servidor
                recipient_id = input("Digite o ID do destinatário (13 dígitos): ")
                if len(recipient_id) != 13:
                    print("O ID do destinatário deve ter exatamente 13 dígitos. \n")
                    return
                message_content = input("Digite o conteúdo da mensagem (máximo de 218 caracteres): ")
                if len(message_content) > 218:
                    print("O conteúdo da mensagem deve ter no máximo 218 caracteres. \n")
                    return
                # Enviar mensagem ao servidor
                self.send_message(recipient_id, message_content)

            elif choice == '2':
                # Verificar se há mensagens do servidor
                self.verify_messages()
                # Submenu para visualizar mensagens trocadas com um ID específico
                while True:
                    print("--------------------")
                    print("Submenu:")
                    print("1. Ver mensagens trocadas com um ID específico")
                    print("9. Voltar ao menu principal")
                    print("--------------------")
                    sub_choice = input("Escolha uma opção: ")
                    if sub_choice == '1':
                        participant_id = input("Digite o ID do participante (13 dígitos): ")
                        if len(participant_id) != 13:
                            print("O ID do participante deve ter exatamente 13 dígitos. \n")
                            continue
                        display_messages_with_id(participant_id)
                    elif sub_choice == '9':
                        break
                    else:
                        print("Opção inválida. Por favor, escolha 1 ou 9. \n")
            
            elif choice == '3':
                while True:
                    print("--------------------")
                    print("Submenu:")
                    print("1. Criar grupo")
                    print("2. Ver grupos existentes")
                    print("3. Enviar mensagem para um grupo")
                    print("9. Voltar ao menu principal")
                    print("--------------------")
                    sub_choice = input("Escolha uma opção: ")
                    if sub_choice == '1':
                        group_name = input("Digite o nome do grupo: ")
                        group_members = input("Digite os IDs dos membros separados por vírgula: ")
                        # Enviar mensagem ao servidor
                        formatted_message = f'04{unique_id}{group_name}{group_members}'
                        self.client_socket.sendall(formatted_message.encode())
                        print("Mensagem enviada ao servidor: ", formatted_message + "\n")
                    elif sub_choice == '2':
                        # Verificar se há mensagens do servidor
                        self.verify_messages()
                    elif sub_choice == '3':
                        group_name = input("Digite o nome do grupo: ")
                        message_content = input("Digite o conteúdo da mensagem (máximo de 218 caracteres): ")
                        # Enviar mensagem ao servidor
                        formatted_message = f'05{unique_id}{group_name}{message_content}'
                        self.client_socket.sendall(formatted_message.encode())
                        print("Mensagem enviada ao servidor: ", formatted_message + "\n")
                    elif sub_choice == '9':
                        break
                    else:
                        print("Opção inválida. Por favor, escolha 1, 2, 3 ou 9. \n")

            elif choice == '9':
                print("Desconectando... \n")
                self.client_socket.close()
                break
            else:
                print("Opção inválida. Por favor, escolha 1, 2 ou 9. \n")

    def start(self):
        
        try:
            # Conectar ao servidor
            self.client_socket.connect((self.host, self.port))
            print(f"Conectado ao servidor em {self.host}:{self.port} \n")

            # Receber mensagem inicial do servidor
            initial_message = self.client_socket.recv(1024).decode()
            print(f"Mensagem do servidor: {initial_message} \n")

            # Enviar '01' para se cadastrar
            message = "01"
            self.client_socket.sendall(message.encode())
            print("Mensagem '01' enviada. \n")

            # Receber o ID único do servidor
            modified_id = self.client_socket.recv(1024).decode()
            print(f"Recebido do servidor: {modified_id} \n")
            unique_id = modified_id[2:]
            print(f"ID único: {unique_id} \n")

            self.chosen_choice()
                
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
            self.client_socket.close()

if __name__ == '__main__':
    input("Pressione Enter para iniciar o cliente... \n")
    port = input("Digite a porta do servidor: ")
    Client('localhost', int(port))
