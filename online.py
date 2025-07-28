import time
import tkinter as tk
from tkinter import messagebox
import webbrowser
import json
import os
from tuya_connector import TuyaOpenAPI


ARQUIVO_DISPOSITIVOS = "meus_dispositivos_online.json" #Json para incluir e organizar os dispositivos
#Dados da nuvem Tuya https://auth.tuya.com
# Carrega as credenciais da Tuya a partir do arquivo acess.json
with open("acess.json", "r", encoding="utf-8") as cred_file:
    creds = json.load(cred_file)

ACCESS_ID = creds["ACCESS_ID"]
ACCESS_KEY = creds["ACCESS_KEY"]
API_ENDPOINT = creds["API_ENDPOINT"]

openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
openapi.connect()

INFRARED_ID = "7478880498f4abfd1111"
REMOTE_ID = "eb166fc111e2b20492c9gq"


#Obter Temperaturas dos sensores
def obter_temp_e_umidade(device_id):
    try:
        if device_id == 'eba0dc1d90fb34ec6dadln':
            res = openapi.get(f"/v2.0/cloud/thing/{device_id}/shadow/properties?codes=temperature,humidity")
            props = {p["code"]: p["value"] for p in res["result"]["properties"]}
            temp = round(props.get("temperature", 0) / 10, 1)
            hum = props.get("humidity", "--")
            return temp, hum
        else:
            status = openapi.get(f"/v1.0/devices/{device_id}/status")
            temp = hum = "--"
            for item in status.get("result", []):
                if item["code"] == "va_temperature":
                    temp = round(item["value"] / 10, 1)
                elif item["code"] == "va_humidity":
                    hum = item["value"]
            return temp, hum

    except Exception as e:
        print(f"Sensor {device_id}: {e}")
        return "--", "--"


def atualizar_temperaturas():
    tq, hq = obter_temp_e_umidade('eb0e1ad772be57841dkef4')
    temp_quarto_label.config(text=f"  Quarto:      {tq}°C  -  {hq}%")

    tb, hb = obter_temp_e_umidade('ebc3878b07207869f23xzd')
    temp_banheiro_label.config(text=f"  Banheiro:   {tb}°C  -  {hb}%")

    tp, hp = obter_temp_e_umidade('eb4466351c3248941d7cg6')
    temp_piscina_label.config(text=f"  Piscina:     {tp}°C  -  {int(hp / 10)}%")

    tl, hl = obter_temp_e_umidade('eba0dc1d90fb34ec6dadln')
    temp_loja_label.config(text=f"  Loja:           {tl}°C  - {hl}%")

    root.after(40000, atualizar_temperaturas)

# CARREGAR DISPOSITIVOS
def carregar_dispositivos():
    if os.path.exists(ARQUIVO_DISPOSITIVOS):
        with open(ARQUIVO_DISPOSITIVOS, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        messagebox.showerror("Erro", f"Arquivo {ARQUIVO_DISPOSITIVOS} não encontrado.")
        return []

def obter_status_dispositivo(device_id):
    try:
        status = openapi.get(f"/v1.0/devices/{device_id}/status")
        return status.get("result", [])
    except Exception as e:
        print(f"[ERRO] ao obter status de {device_id}: {e}")
        return []

def alternar_dispositivo_cloud(dev):
    try:
        status = obter_status_dispositivo(dev['id'])
        atual = next((item['value'] for item in status if item['code'] == dev['code']), False)
        novo_estado = not atual

        if dev['code'] == 'AlarmSwitch':
            comando = {"commands": [{"code": "AlarmSwitch", "value": True}]}
            openapi.post(f"/v1.0/iot-03/devices/{dev['id']}/commands", comando)
            chave = f"{dev['id']}_{dev['code']}"
            label = status_labels.get(chave)
            btn = toggle_buttons.get(chave)

            if label and btn:
                label.config(text="Tocando", fg="blue")
                btn.config(relief="sunken", bg="lightblue")
                root.after(10000, atualizar_status)

        else:
            comando = {"commands": [{"code": dev['code'], "value": novo_estado}]}

        openapi.post(f"/v1.0/iot-03/devices/{dev['id']}/commands", comando)
        root.after(1000, atualizar_status)

    except Exception as e:
        print(f"[ERRO] ao alternar dispositivo {dev['name']}: {e}")


def atualizar_status():
    root.after(30000, atualizar_status)
    for dev in devices:
        chave = f"{dev['id']}_{dev['code']}"
        label = status_labels.get(chave)
        btn = toggle_buttons.get(chave)

        if not label or not dev.get("code"):
            continue

        status = obter_status_dispositivo(dev['id'])
        valor = next((item['value'] for item in status if item['code'] == dev['code']), None)

        if dev.get("tipo") == "cortina":
            try:
                if valor == 100:
                    label.config(text="Aberto", fg="green")
                    btn.config(relief="sunken", bg="lightgreen")
                elif valor == 0:
                    label.config(text="Fechado", fg="red")
                    btn.config(relief="raised", bg="lightcoral")
                elif isinstance(valor, int):
                    label.config(text=f"Parado {valor}%", fg="orange")
                    btn.config(relief="raised", bg="lightyellow")
                else:
                    label.config(text="Desconhecido", fg="gray")
                    btn.config(relief="raised", bg="gray")
            except Exception as e:
                print(f"[ERRO] cortina {dev['name']}: {e}")
                label.config(text="Erro", fg="gray")
                btn.config(relief="raised", bg="gray")

        elif dev.get("tipo") == "portao":
            if valor == True:
                label.config(text="Aberto", fg="green")
                btn.config(relief="sunken", bg="lightgreen")
            else: 
                label.config(text="Fechado", fg="red")
                btn.config(relief="raised", bg="lightcoral")

        elif dev.get("tipo") == "alarme":
                label.config(text=" Ativo ", fg="green")
                btn.config(relief="sunken", bg="lightgreen")

        else:
            if valor in [True, "open", "on"]:
                label.config(text="Ligado", fg="green")
                btn.config(relief="sunken", bg="lightgreen")
            elif valor in [False, "close", "off"]:
                label.config(text="Desligado", fg="red")
                btn.config(relief="raised", bg="lightcoral")
            else:
                label.config(text=str(valor), fg="black")
                btn.config(relief="raised")

def alternar_cortina_cloud(dev):
        status = obter_status_dispositivo(dev['id'])
        percent = next((item['value'] for item in status if item['code'] == 'percent_state'), 0)

        if percent == 100:
            novo_estado = "close"
        else:
            novo_estado = "open"

        comando = {"commands": [{"code": "control", "value": novo_estado}]}

        openapi.post(f"/v1.0/iot-03/devices/{dev['id']}/commands", comando)
        root.after(1000, atualizar_status)


#Para dispositivos do tipo abridor de garagem
def alternar_portao_cloud(dev):
    try:

        status = obter_status_dispositivo(dev['id'])
        atual = next((item['value'] for item in status if item['code'] == dev['code']), False)

        novo_estado = not atual
        comando = {"commands": [{"code": dev["code"], "value": novo_estado}]}

        resposta = openapi.post(f"/v1.0/iot-03/devices/{dev['id']}/commands", comando)
        print(f"[INFO] Comando enviado para {dev['name']} - Resposta: {resposta}")

        chave = f"{dev['id']}_{dev['code']}"
        label = status_labels.get(chave)
        btn = toggle_buttons.get(chave)

        if label and btn:
            label.config(text="Acionando...", fg="blue")
            btn.config(relief="sunken", bg="lightblue")
            root.after(8000, atualizar_status)

    except Exception as e:
        print(f"[ERRO] ao acionar portão {dev['name']}: {e}")


# Sensores Temperatura
def atualizar_status_ar():
    try:
        response = openapi.get(f"/v2.0/infrareds/{INFRARED_ID}/remotes/{REMOTE_ID}/ac/status")
        status_ar = response.get("result", {})

        ligado = status_ar.get("power") == "1"
        temperatura = int(status_ar.get("temp", 24))
        modo_value = status_ar.get("mode")
        wind = status_ar.get("wind")

        modo_text = ""
        modo_color = "black"

        if modo_value == "0":
            modo_text = "Esfriar"
            modo_color = "blue"
        elif modo_value == "1":
            modo_text = "Aquecer"
            modo_color = "red"
        elif modo_value == "2":
            modo_text = "Automatico"
        elif modo_value == "3":
            modo_text = "Ventilar"
        else:
            modo_text = "Humidecer"

        if wind == "0":
            wind = "Automatic"
        elif wind == "1":
            wind = "Baixo"
        elif wind == "2":
            wind = "Medio"
        else:
            wind = "Alto"

        # Retorno Tela
        btn_toggle_ar.config(text=f"{'Desligar' if ligado else 'Ligar'}", bg="lightgreen" if ligado else "#aed6f1")
        status_temp_label.config(text=f"Temp: {temperatura}°C")
        status_modo_label.config(text=f"{modo_text}", fg=modo_color)
        status_wind_label.config(text=f"Volume de ar: {wind}")

        return ligado, temperatura

    except Exception as e:
        status_power_label.config(text="--")
        status_temp_label.config(text="Temp: --°C")
        status_modo_label.config(text="Erro", fg="black")
        status_wind_label.config(text="Volume de ar: --")
        print(f"Falha ao obter status do ar-condicionado: {e}")
        return False, 24


#Ar Condicionado
def enviar_comando_ar(power, temp):
    comandos = {
        "power": 1 if power else 0,
        "temp": temp
    }
    openapi.post(f"/v2.0/infrareds/{INFRARED_ID}/air-conditioners/{REMOTE_ID}/scenes/command", comandos)


def alternar_ar():
    ligado, temperatura = atualizar_status_ar()
    novo_estado = not ligado
    enviar_comando_ar(novo_estado, temperatura)
    root.after(500, atualizar_status_ar)


def aumentar_temp():
    ligado, temperatura = atualizar_status_ar()
    nova_temp = min(temperatura + 1, 30)
    enviar_comando_ar(ligado, nova_temp)
    root.after(500, atualizar_status_ar)


def diminuir_temp():
    ligado, temperatura = atualizar_status_ar()
    nova_temp = max(temperatura - 1, 16)
    enviar_comando_ar(ligado, nova_temp)
    root.after(500, atualizar_status_ar)


def alternar_modo_ar(event=None):
    try:
        response = openapi.get(f"/v2.0/infrareds/{INFRARED_ID}/remotes/{REMOTE_ID}/ac/status")
        status_ar = response.get("result", {})
        ligado = status_ar.get("power") == "1"
        temperatura = int(status_ar.get("temp", 24))
        modo_atual = int(status_ar.get("mode", 0))

        proximo_modo = (modo_atual + 1) % 5

        comandos = {"mode": proximo_modo, "power": 1 if ligado else 0, "temp": temperatura, "wind": "1"}

        openapi.post(f"/v2.0/infrareds/{INFRARED_ID}/air-conditioners/{REMOTE_ID}/scenes/command", comandos)

        root.after(1000, atualizar_status_ar)

    except Exception as e:
        print(f"Falha ao alternar modo do ar: {e}")


def alternar_wind_ar(event=None):
    try:
        response = openapi.get(f"/v2.0/infrareds/{INFRARED_ID}/remotes/{REMOTE_ID}/ac/status")
        status_ar = response.get("result", {})

        ligado = status_ar.get("power") == "1"
        temperatura = int(status_ar.get("temp", 24))
        modo = int(status_ar.get("mode", 0))
        wind_atual = int(status_ar.get("wind", 0))

        proximo_wind = (wind_atual + 1) % 4

        comandos = {"power": 1 if ligado else 0, "temp": temperatura, "mode": modo, "wind": proximo_wind}

        openapi.post(
            f"/v2.0/infrareds/{INFRARED_ID}/air-conditioners/{REMOTE_ID}/scenes/command",
            comandos
        )

        root.after(1000, atualizar_status_ar)

    except Exception as e:
        print(f"[ERRO] Falha ao alternar wind do ar: {e}")


def desligar_tv_e_pc():
        comando = {"commands": [{"code": "switch_1", "value": False}]}

        openapi.post(f"/v1.0/devices/20087058f5cfa25fc71b/commands", comando)
        time.sleep(1)
        os.system("shutdown /s /t 1")


# Interface Tkinter
root = tk.Tk()
root.title("Controle de Dispositivos Tuya Online by MHPS.com.br")
root.geometry("500x900")
root.resizable(True, True)
root.configure(bg="#B0E0E6")

tk.Label(root, text="Controle de Dispositivos", bg="#B0E0E6", font=("Arial", 14)).pack(pady=2)

#Dados dos Sensores
sensor_frame = tk.Frame(root)
sensor_frame.pack(pady=1)

temp_quarto_label = tk.Label(sensor_frame, text="Quarto: --", bg="#B0E0E6", font=("Arial", 13), width=23, anchor="w")
temp_quarto_label.grid(row=0, column=0, padx=2, pady=1)

temp_banheiro_label = tk.Label(sensor_frame, text="Banheiro: --", bg="#B0E0E6", font=("Arial", 13), width=23, anchor="w")
temp_banheiro_label.grid(row=0, column=1, padx=2, pady=1)

temp_piscina_label = tk.Label(sensor_frame, text="Piscina: --", bg="#B0E0E6", font=("Arial", 13), width=23, anchor="w")
temp_piscina_label.grid(row=1, column=0, padx=2, pady=1)

temp_loja_label = tk.Label(sensor_frame, text="Loja: --", bg="#B0E0E6", font=("Arial", 13), width=23, anchor="w")
temp_loja_label.grid(row=1, column=1, padx=2, pady=1)

atualizar_temperaturas()

#Botoes Ar-condicionado
frame_ar = tk.Frame(root,  bg="#B0E0E6")
frame_ar.pack(pady=5)

linha_botoes_ar = tk.Frame(frame_ar,  bg="#B0E0E6")
linha_botoes_ar.pack()

btn_toggle_ar = tk.Button(linha_botoes_ar, text="Ligar/Desligar", width=15, bg="#aed6f1", command=alternar_ar)
btn_toggle_ar.pack(side="left", padx=20)

btn_temp_mais = tk.Button(linha_botoes_ar, text="+", width=5, bg="#FF4500", command=aumentar_temp)
btn_temp_mais.pack(side="left", padx=10)

btn_temp_menos = tk.Button(linha_botoes_ar, text="−", width=5, bg="#00BFFF", command=diminuir_temp)
btn_temp_menos.pack(side="left", padx=10)

status_ar_labels_frame = tk.Frame(frame_ar, bg="#B0E0E6")
status_ar_labels_frame.pack(pady=5)

status_power_label = tk.Label(status_ar_labels_frame, bg="#B0E0E6", text="", font=("Arial", 11))
status_power_label.pack(side="left", padx=2)

status_temp_label = tk.Label(status_ar_labels_frame, bg="#B0E0E6", text="", font=("Arial", 11))
status_temp_label.pack(side="left", padx=2)

status_modo_label = tk.Label(status_ar_labels_frame, bg="#B0E0E6", text="", font=("Arial", 11))
status_modo_label.pack(side="left", padx=2)
status_modo_label.bind("<Button-1>", alternar_modo_ar)

status_wind_label = tk.Label(status_ar_labels_frame, bg="#B0E0E6", text="", font=("Arial", 11))
status_wind_label.pack(side="left", padx=2)
status_wind_label.bind("<Button-1>", alternar_wind_ar)

atualizar_status_ar()

status_labels = {}
toggle_buttons = {}

devices = carregar_dispositivos()

device_frame = tk.Frame(root)
device_frame.pack(pady=5)

colunas = 2
linha = 0
coluna = 0

for dev in devices:
    frame = tk.Frame(device_frame, bg="#B0E0E6", padx=5, pady=5, bd=1, relief="ridge")
    frame.grid(row=linha, column=coluna, padx=1, pady=1, sticky="n")

    label_nome = tk.Label(frame, bg="#B0E0E6", text=dev["name"], font=("Arial", 10), width=12, anchor="e")
    label_nome.grid(row=0, column=0, padx=5, pady=2, sticky="e")

    if dev.get("tipo") == "cortina":
        btn = tk.Button(frame, text="Abre/Fecha", width=10, height=1, bg="lightgray", command=lambda d=dev: alternar_cortina_cloud(d))
    elif dev.get("tipo") == "portao":
        btn = tk.Button(frame, text="Abrir Portão", width=10, height=1, bg="lightgray", command=lambda d=dev: alternar_portao_cloud(d))
    else:
        btn = tk.Button(frame, text="Liga/Desliga", width=10, height=1, bg="lightgray", command=lambda d=dev: alternar_dispositivo_cloud(d))
    btn.grid(row=0, column=1, padx=5, pady=2, sticky="w")

    status = tk.Label(frame, bg="#B0E0E6", text="Status", font=("Arial", 9))
    status.grid(row=1, column=0, columnspan=2, pady=3)

    status = tk.Label(frame, bg="#B0E0E6", text="Status", font=("Arial", 9))
    status.grid(row=1, column=0, columnspan=2, pady=3)

    chave = f"{dev['id']}_{dev['code']}"
    status_labels[chave] = status
    toggle_buttons[chave] = btn

    coluna += 1
    if coluna >= colunas:
        coluna = 0
        linha += 1

# Preencher com frame vazio se número de dispositivos for ímpar
if len(devices) % colunas != 0:
    frame_vazio = tk.Frame(device_frame, bg="#B0E0E6", width=213, height=67)
    frame_vazio.grid(row=linha, column=coluna, padx=1, pady=1)

# Botão Desligar TV + PC
btn_desligar_tv_pc = tk.Button(root, text="Desligar TV + PC", bg="red", fg="white", font=("Arial", 12), width=20, command=desligar_tv_e_pc)
btn_desligar_tv_pc.pack(pady=5)

#Link Pagina
def abrir_link(url):
    webbrowser.open_new_tab(url)

link = tk.Label(text="Desenvolvido por MHPS", bg="#B0E0E6", fg="blue", cursor="hand2")
link.pack(pady=20)
link.bind("<Button-1>", lambda e: abrir_link("https://www.mhps.com.br"))

atualizar_status()
root.mainloop()
