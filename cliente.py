import threading, socket 

# Variáveis de configuração
IP = '127.0.0.1'  # Endereço IP do servidor
PORTA = 3000  # Porta do servidor

def receive_message(sock):
    while True:
        data = sock.recv(1024)
        print(data)

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        
        s.connect((IP, PORTA))
        
        receive_thread = threading.Thread(target=receive_message, args=(s,))
        receive_thread.start()
        
        receive_thread.join()
