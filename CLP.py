# Bibliotecas
from asyncua.common.subscription import SubHandler
from asyncua import Client
from dotenv import load_dotenv
import asyncio
import os
import socket
import threading
import queue
import time

# Variáveis de ambiente
load_dotenv()
ENDPOINT_SERVIDOR_OPC = os.getenv("ENDPOINT_SERVIDOR_OPC")
IP = os.getenv("IP")
PORTA = int(os.getenv("PORTA"))
NODE_ID_TEMPERATURA = os.getenv("NODE_ID_TEMPERATURA")
NODE_ID_REFERENCIA = os.getenv("NODE_ID_REFERENCIA")
NODE_ID_FLUXO_DE_CALOR = os.getenv("NODE_ID_FLUXO_DE_CALOR")
NODE_ID_CONSTANTE_KP = os.getenv("NODE_ID_CONSTANTE_KP")
NODE_ID_CONSTANTE_KI = os.getenv("NODE_ID_CONSTANTE_KI")

# Lista para armazenar os sockets dos clientes conectados
clientes_conectados = []
clientes_lock = threading.Lock()

# Handler para exibir os dados de todos os nós no terminal
class handler(SubHandler):
    def __init__(self, data_queue):
        self._data_queue = data_queue

    async def obter_nome(self, node):
        nome = await node.read_attribute(4)
        return nome.Value.Value.Text

    async def datachange_notification(self, node, valor, data):
        data_e_hora = data.monitored_item.Value.SourceTimestamp.strftime("%d/%m/%Y %H:%M:%S")
        nome = await self.obter_nome(node)
        if valor is not None and data_e_hora is not None:
            message = f"[{data_e_hora}] {nome}: {valor}"
            print(message)
            self._data_queue.put(message)  # Use put em vez de await

async def criar_e_subscrever(cliente, node, handler):
    sub = await cliente.create_subscription(period=0.0, handler=handler)
    await sub.subscribe_data_change(node)
    return sub

# Função para subscrever às mudanças em todos os nós
async def subscrever_opc(data_queue):
    async with Client(url=ENDPOINT_SERVIDOR_OPC) as cliente:
        subs = {}
        ids = {
            "fluxo": NODE_ID_FLUXO_DE_CALOR,
            "temperatura": NODE_ID_TEMPERATURA,
            "referencia": NODE_ID_REFERENCIA,
            "kp": NODE_ID_CONSTANTE_KP,
            "ki": NODE_ID_CONSTANTE_KI,
        }
        obj = {nome: cliente.get_node(node_id) for nome, node_id in ids.items()}
        for nome, node in obj.items():
            subs[nome] = await criar_e_subscrever(cliente, node, handler(data_queue))
        while True:
            await asyncio.sleep(0.05)

# Função do servidor TCP/IP
def tcp_ip_server(data_queue):
    global clientes_conectados
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, 3000))
    server_socket.listen(5)
    print(f"Servidor TCP/IP escutando em {IP}:{PORTA}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexão aceita de {addr}")
        with clientes_lock:
            clientes_conectados.append(client_socket)
        client_handler = threading.Thread(target=handle_client, args=(client_socket, data_queue))
        client_handler.start()

def handle_client(client_socket, data_queue):
    global clientes_conectados
    while True:
        try:
            # Verifica se há dados na fila
            if not data_queue.empty():
                message = data_queue.get_nowait()
                with clientes_lock:
                    for client in clientes_conectados:
                        try:
                            client.sendall(message.encode('utf-8'))
                        except (socket.error, BrokenPipeError):
                            print("Erro de conexão, removendo cliente.")
                            clientes_conectados.remove(client)
            else:
                time.sleep(0.1)
        except (socket.error, BrokenPipeError):
            print("Erro de conexão, fechando o socket.")
            with clientes_lock:
                if client_socket in clientes_conectados:
                    clientes_conectados.remove(client_socket)
            client_socket.close()
            break

# Main
if __name__ == "__main__":
    data_queue = queue.Queue()
    opc_task = threading.Thread(target=lambda: asyncio.run(subscrever_opc(data_queue)))
    opc_task.start()
    tcp_ip_server(data_queue)
