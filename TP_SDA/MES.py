# Bibliotecas
from asyncua.common.subscription import SubHandler
from asyncua import Client
from dotenv import load_dotenv
import asyncio, os

# Variáveis de ambiente
load_dotenv()
ENDPOINT_SERVIDOR_OPC = os.getenv("ENDPOINT_SERVIDOR_OPC")
NODE_ID_TEMPERATURA = os.getenv("NODE_ID_TEMPERATURA")

# Handler para exibir os dados de temperatura no arquivo
class handler_temperatura(SubHandler):
    async def datachange_notification(self, node, valor, data):
        data_e_hora = data.monitored_item.Value.SourceTimestamp.strftime("%d/%m/%Y %H:%M:%S")
        if isinstance(valor, (int, float)) and data_e_hora:
            novo_registro = f"[{data_e_hora}] Temperatura: {valor} K\n"
            try:
                with open("./mes.txt", "a") as arquivo:
                    arquivo.write(novo_registro)
            except OSError as erro:
                print(f"Erro ao escrever no arquivo: {erro}")

# Função para subscrever às mudanças no nó de temperatura
async def subscrever_temperatura_opc():
    try:
        async with Client(url=ENDPOINT_SERVIDOR_OPC) as cliente:
            try:
                sub = await cliente.create_subscription(period = 0.0, handler = handler_temperatura())
                await sub.subscribe_data_change(cliente.get_node(NODE_ID_TEMPERATURA))
                while (1):
                    await asyncio.sleep(0.05)
            except Exception as erro:
                print(f"Erro ao configurar a subscrição OPC: {erro}")
    except Exception as erro:
        print(f"Erro ao conectar ao servidor OPC: {erro}")

# Main
if __name__ == "__main__":
    print(f"Os dados são registrados no arquivo mes.txt")
    asyncio.run(subscrever_temperatura_opc())
