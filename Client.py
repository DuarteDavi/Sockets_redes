import socket
import time
import datetime

class Client:
    def __init__(self, host, port):
        self.port = port
        self.host = host
        
        # Criar um socket TCP
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Definir timeout
        self.client_socket.settimeout(10.0)  # Timeout de 10 segundos

        # Dicionário para armazenar mensagens trocadas entre IDs
        self.messages_dict = {}
        
        # Armazena confirmações de entrega
        self.delivery_confirmations = {} 
        
        self.start()

            
        
    def __convert_timestamp(self, timestamp):
            # Converter o timestamp Unix para um objeto datetime
            dt_object = datetime.datetime.fromtimestamp(timestamp)
            
            # Formatar o objeto datetime para uma string legível
            human_readable_time = dt_object.strftime('%H:%M:%S em %d/%m/%Y')
            
            return human_readable_time

    def __display_messages_with_id(self, participant_id):
            if participant_id in self.messages_dict:
                print(f"Mensagens trocadas com {participant_id}:")
                for msg in self.messages_dict[participant_id]:
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
    # Envio de confirmação de leitura
    def send_read_confirmation(self, src_id):
            timestamp = int(time.time())
            confirmation_message = f"08{src_id}{str(timestamp).ljust(10)}\n"
            self.client_socket.sendall(confirmation_message.encode())
            print(f"Mensagem de confirmação de leitura enviada: {confirmation_message} \n")
    
    # Envio de mensagem
    def send_message(self, recipient_id, message_content=""):
        timestamp = int(time.time())
        # Formatar a mensagem com '03', o ID do cliente, ID do destinatário, timestamp e conteúdo da mensagem
        formated_unique_id = self.unique_id.replace("\n", "").replace(" ", "")
        recipient_id = recipient_id.replace("\n", "").replace(" ", "")
        formatted_message = f'{"03"}{formated_unique_id}{recipient_id}{str(timestamp).ljust(10)}{message_content.replace(" ", "_")}\n'
        self.client_socket.sendall(formatted_message.encode())
        print("Mensagem enviada ao servidor: ", formatted_message + "\n")

        # Armazenar a mensagem enviada
        if recipient_id not in self.messages_dict:
            self.messages_dict[recipient_id] = []
        self.messages_dict[recipient_id].append(f"Enviado para {recipient_id} em {self.__convert_timestamp(timestamp)}: {message_content}")
    
    # Envio de mensagem para grupo
    def send_message_to_group(self, group_id, message_content=""):
        timestamp = int(time.time())
        # Formatar a mensagem com '03', o ID do cliente, ID do grupo, timestamp e conteúdo da mensagem
        formated_unique_id = self.unique_id.replace("\n", "").replace(" ", "")
        group_id = group_id.replace("\n", "").replace(" ", "")
        formatted_message = f'{"03"}{formated_unique_id}{group_id}{str(timestamp).ljust(10)}{message_content.replace(" ", "_")}\n'
        self.client_socket.sendall(formatted_message.encode())
        print("Mensagem enviada ao servidor: ", formatted_message + "\n")

        # Armazenar a mensagem enviada
        if group_id not in self.messages_dict:
            self.messages_dict[group_id] = []
        self.messages_dict[group_id].append(f"Enviado para {group_id} em {self.__convert_timestamp(timestamp)}: {message_content}")
    
    # Criação de grupo
    def create_group(self, members):
        timestamp = int(time.time())
        # Formatar a mensagem com '10', o ID do cliente, timestamp e membros do grupo
        formated_unique_id = self.unique_id.replace("\n", "").replace(" ", "")
        formatted_message = f'{"10"}{formated_unique_id}{str(timestamp).ljust(10)}{members}\n'
        self.client_socket.sendall(formatted_message.encode())
        print("Mensagem enviada ao servidor: ", formatted_message + "\n")
        self.verify_messages()

    def verify_messages(self):
        try:
            data = self.client_socket.recv(1024).decode()
            if data:
                messages = data.split("\n")
                # Filtra a lista para remover os elementos vazios
                messages = [msg for msg in messages if msg]
                print(messages)
                print('\n|||------messages------|||')
                # Processar todas as mensagens recebidas
                for message in messages:
                    message = message.strip()
                    if message.startswith("Sucesso") or message.startswith("Erro"):
                        print(f"Resposta do servidor: {message} \n")
                    # Processar confirmação de entrega    
                    elif message.startswith("07"):
                        print('Erro 7')
                        cod = message[:2]
                        dst = message[2:15]
                        timestamp_str = message[15:25].strip()
                        timestamp = int(timestamp_str)
                        
                        print(f"Confirmação de entrega: Mensagens enviadas para {dst} até {self.__convert_timestamp(timestamp)} foram entregues. \n")
                        
                        try:
                            # Atualizar mensagens enviadas para o destinatário
                            if dst in self.messages_dict:
                                self.messages_dict[dst] = [msg for msg in self.messages_dict[dst] if int(msg.split(' em ')[1].split(':')[0]) <= timestamp]
                        except ValueError:
                            print('07.message:', message)
                            print(f"Erro ao converter o timestamp: {timestamp_str} \n")
                            
                    # Confirmação de leitura
                    elif message.startswith("08"):
                        print('Erro 8')
                        cod = message[:2]
                        src_id = message[2:15].strip()
                        timestamp_str = message[15:25].strip()

                        try:
                            timestamp = int(timestamp_str)
                            print(f"Confirmação de leitura recebida de {src_id} para mensagem enviada em {self.__convert_timestamp(timestamp)} \n")
                            
                            # Enviar notificação de leitura para o cliente originador
                            notification_message = f"09{src_id}{timestamp_str}\n"
                            self.client_socket.sendall(notification_message.encode())
                            print(f"Notificação de leitura enviada para {src_id}: {notification_message} \n")
                        except ValueError:
                            print(f"Erro ao converter o timestamp: '{timestamp_str}' \n")
                            
                    # Notificação de leitura
                    elif message.startswith("09"):
                        print('Erro 9')
                        cod = message[:2]
                        src_id = message[2:15].strip()
                        timestamp_str = message[15:25].strip()

                        try:
                            timestamp = int(timestamp_str)
                            print(f"Notificação de leitura: Mensagem enviada para {src_id} foi lida em {self.__convert_timestamp(timestamp)} \n")
                            # Armazenar a mensagem recebida
                            if src_id not in self.messages_dict:
                                self.messages_dict[src_id] = []
                            self.messages_dict[src_id].append(f"Recebido de {src_id} em {self.__convert_timestamp(timestamp)}")
                        except ValueError:
                            print(f"Erro ao converter o timestamp: '{timestamp_str}' \n")
                            
                    # Processar confirmação de entrega de grupo
                    elif message.startswith("11"):
                        print('Erro 11')
                        cod = message[:2]
                        group_id = message[2:15]
                        timestamp_str = message[15:25].strip()
                        timestamp = int(timestamp_str)
                        
                        print(f"Confirmação de entrega: Grupo {group_id} criado até {self.__convert_timestamp(timestamp)}.")
                        print(f"ID do grupo: {group_id}")

                        try:
                            # Atualizar mensagens enviadas para o destinatário
                            if group_id in self.messages_dict:
                                self.messages_dict[group_id] = [msg for msg in self.messages_dict[group_id] if int(msg.split(' em ')[1].split(':')[0]) <= timestamp]
                        except ValueError:
                            print('11.message:', message)
                            print(f"Erro ao converter o timestamp: {timestamp_str} \n")
                    else:
                        print('Erro Else')
                        # Processar mensagem recebida (resposta do servidor com dados de quem enviou e data)
                        src_id = message[2:15].strip()  # ID do remetente
                        timestamp_str = message[28:38].strip()  # Timestamp
                        message_data = message[38:].strip().replace("_", " ")  # Conteúdo da mensagem
                        #message_data = message_message[:-25]

                        try:
                            timestamp = int(timestamp_str)
                            print(f"Mensagem recebida de {src_id} em {self.__convert_timestamp(timestamp)}: {message_data} ")

                            # Armazenar a mensagem recebida
                            if src_id not in self.messages_dict:
                                self.messages_dict[src_id] = []
                            self.messages_dict[src_id].append(f"Recebido de {src_id} em {self.__convert_timestamp(timestamp)}: {message_data}")
                            self.send_read_confirmation(src_id)
                        except ValueError:
                            print('000.message:', message)
                            print(f"Erro ao converter o timestamp: {timestamp_str} \n")
                print('|||------end-of-messages------|||\n')
            else:
                print("Nenhuma mensagem recebida. \n")
        except :
            print("Nenhuma mensagem recebida. \n")
    
    def chosen_choice(self):
        timestamp = int(time.time())
        while True:
            choice = self.choices()
            # Enviar mensagem ao servidor
            if choice == '1':
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

            # Verificar se há mensagens do servidor
            elif choice == '2':
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
                        self.__display_messages_with_id(participant_id)
                    elif sub_choice == '9':
                        break
                    else:
                        print("Opção inválida. Por favor, escolha 1 ou 9. \n")
            
            # Submenu para grupos
            elif choice == '3':
                while True:
                    print("--------------------")
                    print("Submenu:")
                    print("1. Criar grupo")
                    print("2. Enviar mensagem para um grupo")
                    print("9. Voltar ao menu principal")
                    print("--------------------")
                    sub_choice = input("Escolha uma opção: ")
                    # Criar grupo
                    if sub_choice == '1':
                        group_members = input("Digite os IDs dos membros separados por vírgula: ")
                        # Enviar mensagem ao servidor
                        self.create_group(group_members)

                    # Enviar mensagem para um grupo
                    elif sub_choice == '2':
                        group_id = input("Digite o id do grupo: ")
                        message_content = input("Digite o conteúdo da mensagem (máximo de 218 caracteres): ")
                        self.send_message_to_group(group_id, message_content)
                        self.verify_messages()
                    elif sub_choice == '9':
                        break
                    else:
                        print("Opção inválida. Por favor, escolha 1, 2, 3 ou 9. \n")

            # Encerrar o programa
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
            print(modified_id)
            print(f"Recebido do servidor: {modified_id} \n")
            self.unique_id = modified_id[2:]
            print(f"ID único: {self.unique_id} \n")

            self.chosen_choice()
                
        finally:
            self.client_socket.close()

if __name__ == '__main__':
    input("Pressione Enter para iniciar o cliente... \n")
    port = input("Digite a porta do servidor: ")
    Client('25.62.205.242', 2620)
