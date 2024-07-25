# Bibliotecas
from dotenv import load_dotenv
from asyncua import Client
import asyncio, os, threading, time
import matplotlib.pyplot as plt

# Carregar variáveis de ambiente
load_dotenv()
ENDPOINT_SERVIDOR_OPC = os.getenv("ENDPOINT_SERVIDOR_OPC")
NODE_ID_TEMPERATURA = os.getenv("NODE_ID_TEMPERATURA")
NODE_ID_REFERENCIA = os.getenv("NODE_ID_REFERENCIA")
NODE_ID_FLUXO_DE_CALOR = os.getenv("NODE_ID_FLUXO_DE_CALOR")
NODE_ID_CONSTANTE_KP = os.getenv("NODE_ID_CONSTANTE_KP")
NODE_ID_CONSTANTE_KI = os.getenv("NODE_ID_CONSTANTE_KI")

# Parâmetros
C_m = 1000
T_amb = 25
R = 50
dt_simulacao = 1
dt_controle = 0.5
KP = 51
KI = 1

# Variáveis globais
temperatura = T_amb
fluxo_de_calor = 0
erro_anterior = 0
integral_erro = 0
T_ref = 100 # Referência
lock = threading.Lock()

# Listas para armazenar os valores de temperatura e tempo
temperaturas = []
tempos = []
tempo_simulacao = 0

# Função para calcular a derivada da temperatura
def derivada_temperatura(T, Q):
    return (Q / C_m) - ((T - T_amb) / R)

# Método Runge-Kutta de 4ª ordem
def runge_kutta_4(T, Q, dt):
    k1 = derivada_temperatura(T, Q)
    k2 = derivada_temperatura(T + 0.5 * dt * k1, Q)
    k3 = derivada_temperatura(T + 0.5 * dt * k2, Q)
    k4 = derivada_temperatura(T + dt * k3, Q)
    return T + (k1 + 2 * k2 + 2 * k3 + k4) / 6.0 * dt

# Função que implementa o controlador PI
def controle(erro):
    global erro_anterior, integral_erro
    integral_erro += erro * dt_controle
    saida = KP * erro + KI * integral_erro
    erro_anterior = erro
    return saida

# Função que escreve os valores nos nós OPC
async def escrita_opc(nomes, valores):
    async with Client(url=ENDPOINT_SERVIDOR_OPC) as cliente:
        for nome, valor in zip(nomes, valores):
            try:
                await cliente.get_node(nome).write_value(float(valor))
            except Exception as erro:
                print(f"Erro ao escrever o {valor} no nó {nome}: {erro}")

# Função que lê os valores dos nós OPC
async def leitura_opc(nomes):
    valores = []
    async with Client(url=ENDPOINT_SERVIDOR_OPC) as cliente:
        for nome in nomes:
            try:
                valor = await cliente.get_node(nome).read_value()
                valores.append(valor)
            except Exception as erro:
                print(f"Erro ao ler o nó {nome}: {erro}")
    return valores

# Função que simula o funcionamento do alto-forno
def alto_forno():
    global temperatura, fluxo_de_calor, tempo_simulacao
    while (1):
        with lock:
            temperatura = runge_kutta_4(temperatura, fluxo_de_calor, dt_simulacao)
            tempo_simulacao += dt_simulacao
            temperaturas.append(temperatura)
            tempos.append(tempo_simulacao)
        asyncio.run(escrita_opc([NODE_ID_TEMPERATURA, NODE_ID_FLUXO_DE_CALOR], [temperatura, fluxo_de_calor]))
        novo_registro = (f"[SIMULACAO]: Temperatura = {temperatura} K | Fluxo de Calor = {fluxo_de_calor} W\n")
        print(novo_registro)
        time.sleep(dt_simulacao)

# Função que controla a temperatura do alto-forno
def controle_temperatura():
    global fluxo_de_calor
    while (1):
        with lock:
            erro = T_ref - temperatura
            fluxo_de_calor = controle(erro)
        novo_registro = f"[CONTROLE]: Erro = {erro} | Fluxo de Calor Ajustado = {fluxo_de_calor} W\n"
        print(novo_registro)
        time.sleep(dt_controle)

# Função para plotar o gráfico de temperatura ao longo do tempo
def plotar_grafico(tempos, temperaturas):
    plt.plot(tempos, temperaturas)
    plt.xlabel('Tempo (s)')
    plt.ylabel('Temperatura (K)')
    plt.title('Temperatura do Alto-Forno ao Longo do Tempo')
    plt.grid(True)
    plt.show()

# Main
if __name__ == "__main__":
    asyncio.run(escrita_opc([NODE_ID_CONSTANTE_KP, NODE_ID_CONSTANTE_KI, NODE_ID_REFERENCIA], [KP, KI, T_amb]))

    thread_simulacao = threading.Thread(target=alto_forno)
    thread_controle = threading.Thread(target=controle_temperatura)
    thread_simulacao.start()
    thread_controle.start()
    
    time.sleep(120)
    
    plotar_grafico(tempos, temperaturas)
    
    thread_simulacao.join()
    thread_controle.join()
