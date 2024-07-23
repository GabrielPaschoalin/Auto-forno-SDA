# Bibliotecas
from asyncua.common.subscription import SubHandler
from asyncua import Client
from dotenv import load_dotenv
import asyncio, os

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

# Handler para exibir os dados de todos os nós no terminal
class handler(SubHandler):
    def __init__(self):
        self._queue = asyncio.Queue()
    async def obter_nome(self, node):
        nome = await node.read_attribute(4)
        return nome.Value.Value.Text
    async def datachange_notification(self, node, valor, data):
        data_e_hora = data.monitored_item.Value.SourceTimestamp.strftime("%d/%m/%Y %H:%M:%S")
        nome = await self.obter_nome(node)
        if valor is not None and data_e_hora is not None:
            print(f"[{data_e_hora}] {nome}: {valor}")

async def criar_e_subscrever(cliente, node, handler):
    sub = await cliente.create_subscription(period = 0.0, handler = handler)
    await sub.subscribe_data_change(node)
    return sub

# Função para subscrever às mudanças em todos os nós
async def subscrever_opc():
    async with Client(url=ENDPOINT_SERVIDOR_OPC) as cliente:
        subs = {}
        ids = {
            "fluxo": NODE_ID_FLUXO_DE_CALOR,
            "temperatura": NODE_ID_TEMPERATURA,
            "referencia": NODE_ID_REFERENCIA,
            "kp": NODE_ID_CONSTANTE_KP,
            "ki": NODE_ID_CONSTANTE_KI,
        }
        obj = { nome: cliente.get_node(node_id) for nome, node_id in ids.items() }
        for nome, node in obj.items():
            subs[nome] = await criar_e_subscrever(cliente, node, handler())
        while (1):
            await asyncio.sleep(0.05)

# Main
if __name__ == "__main__":
    asyncio.run(subscrever_opc())
