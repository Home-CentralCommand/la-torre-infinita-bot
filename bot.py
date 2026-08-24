import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import json
import os
import requests
import base64
import random
import time

TOKEN = "8900609729:AAHiqL3g7eRVbZtDE-wLg9sGEUfATe7RwNo"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "Home-CentralCommand/la-torre-infinita-bot"
FILE_PATH_PROGRESS = "progreso.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ---------- PERSISTENCIA EN GITHUB ----------
def github_get(file_path):
    if not GITHUB_TOKEN: return None
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()["content"]).decode()
            return content
        else:
            return None
    except:
        return None

def github_put(file_path, content):
    if not GITHUB_TOKEN: return
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    sha = None
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except:
        pass
    encoded = base64.b64encode(content.encode()).decode()
    body = {"message": f"Update {file_path}", "content": encoded}
    if sha:
        body["sha"] = sha
    requests.put(url, headers=headers, json=body)

def cargar_progreso():
    data = github_get(FILE_PATH_PROGRESS)
    if data:
        try:
            return json.loads(data)
        except:
            pass
    return {}

def guardar_progreso():
    github_put(FILE_PATH_PROGRESS, json.dumps(progreso, indent=2))

# ---------- DATOS DEL JUEGO ----------
monstruos = [
    {"nombre": "Alma Errante", "emoji": "🧟", "vida": 20, "daño": 5, "oro": 10, "xp": 5},
    {"nombre": "Orco Salvaje", "emoji": "🧌", "vida": 30, "daño": 8, "oro": 15, "xp": 8},
    {"nombre": "Demonio Menor", "emoji": "👹", "vida": 40, "daño": 12, "oro": 20, "xp": 12},
    {"nombre": "Wyrm Sombrío", "emoji": "🐉", "vida": 55, "daño": 15, "oro": 30, "xp": 15},
    {"nombre": "Caballero Caído", "emoji": "⚔️", "vida": 70, "daño": 18, "oro": 40, "xp": 18},
    {"nombre": "Liche Maligno", "emoji": "🪄", "vida": 90, "daño": 22, "oro": 55, "xp": 22},
]

jefes = [
    {"nombre": "Señor de las Sombras", "emoji": "👑", "vida": 120, "daño": 25, "oro": 80, "xp": 35},
]

# ---------- INICIALIZACIÓN ----------
progreso = cargar_progreso()

# ---------- RUTA FLASK ----------
@app.route('/')
def home():
    return "Bot running"

# ---------- COMANDO /torre ----------
@bot.message_handler(commands=['torre'])
def iniciar_torre(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ 𝗘𝗦𝗧𝗘 𝗝𝗨𝗘𝗚𝗢 𝗦𝗢𝗟𝗢 𝗙𝗨𝗡𝗖𝗜𝗢𝗡𝗔 𝗘𝗡 𝗚𝗥𝗨𝗣𝗢𝗦")
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id not in progreso:
        progreso[user_id] = {
            "nombre": message.from_user.first_name,
            "oro": 0,
            "piso_maximo": 0,
            "experiencia": 0,
            "piso_actual": 1,
            "arma_daño": 10,
            "pociones": 1,
            "partida": {
                "vida": 100,
                "piso": 1,
                "arma_daño": 10,
                "pociones": 1,
                "monstruo_actual": None
            }
        }
        guardar_progreso()
    else:
        # Si ya existe, reiniciamos la partida activa
        progreso[user_id]["partida"] = {
            "vida": 100,
            "piso": 1,
            "arma_daño": 10,
            "pociones": progreso[user_id].get("pociones", 1),
            "monstruo_actual": None
        }
        guardar_progreso()

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚔️ 𝗖𝗢𝗠𝗘𝗡𝗭𝗔𝗥", callback_data="iniciar_aventura"),
        InlineKeyboardButton("📜 𝗚𝗨𝗜𝗔", callback_data="ver_guia")
    )

    bot.send_message(chat_id,
        "🗼 𝗟𝗔 𝗧𝗢𝗥𝗥𝗘 𝗜𝗡𝗙𝗜𝗡𝗜𝗧𝗔\n\n"
        "Bienvenido, aventurero.\n\n"
        "Tu misión es subir pisos venciendo\n"
        "monstruos que bloquean cada puerta.\n\n"
        "Cada 5 pisos hay un jefe.\n"
        "Cada 10 pisos hay un jefe final.\n\n"
        "Gana oro, experiencia y armas.\n\n"
        "¿Listo para empezar?",
        reply_markup=markup
    )

# ---------- GUIA ----------
@bot.callback_query_handler(func=lambda call: call.data == "ver_guia")
def ver_guia(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "📜 𝗚𝗨𝗜𝗔 𝗗𝗘 𝗟𝗔 𝗧𝗢𝗥𝗥𝗘\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚔️ 𝗔𝗧𝗔𝗖𝗔𝗥\n"
        "Daño normal al monstruo.\n\n"
        "🛡️ 𝗗𝗘𝗙𝗘𝗡𝗗𝗘𝗥\n"
        "Reduce el daño recibido.\n\n"
        "✨ 𝗠𝗔𝗚𝗜𝗔\n"
        "Daño masivo, pero puede fallar.\n\n"
        "💊 𝗣𝗢𝗖𝗜𝗢𝗡\n"
        "Recupera 50 puntos de vida.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🏆 𝗢𝗕𝗝𝗘𝗧𝗜𝗩𝗢\n"
        "Subir lo más alto posible.\n"
        "Cada piso es más difícil.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📌 𝗖𝗢𝗠𝗔𝗡𝗗𝗢𝗦\n\n"
        "▸ /torre - Iniciar\n"
        "▸ /miprogreso - Ver progreso\n"
        "▸ /rank - Ranking"
    )

# ---------- INICIAR AVENTURA ----------
@bot.callback_query_handler(func=lambda call: call.data == "iniciar_aventura")
def iniciar_aventura(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    if user_id not in progreso:
        bot.send_message(call.message.chat.id, "❌ 𝗡𝗢 𝗛𝗔𝗬 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗔𝗖𝗧𝗜𝗩𝗔")
        return

    partida = progreso[user_id].get("partida")
    if not partida:
        partida = {
            "vida": 100,
            "piso": 1,
            "arma_daño": 10,
            "pociones": progreso[user_id].get("pociones", 1),
            "monstruo_actual": None
        }
        progreso[user_id]["partida"] = partida
        guardar_progreso()

    mostrar_piso(call.message, user_id)

def mostrar_piso(message, user_id):
    partida = progreso[user_id]["partida"]
    piso = partida["piso"]

    if piso % 10 == 0:
        monstruo = jefes[0].copy()
    else:
        monstruo = random.choice(monstruos).copy()

    partida["monstruo_actual"] = monstruo
    guardar_progreso()

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚔️ 𝗔𝗧𝗔𝗖𝗔𝗥", callback_data="accion_atacar"),
        InlineKeyboardButton("🛡️ 𝗗𝗘𝗙𝗘𝗡𝗗𝗘𝗥", callback_data="accion_defender"),
        InlineKeyboardButton("✨ 𝗠𝗔𝗚𝗜𝗔", callback_data="accion_magia"),
        InlineKeyboardButton("💊 𝗣𝗢𝗖𝗜𝗢𝗡", callback_data="accion_pocion")
    )

    bot.send_message(message.chat.id,
        f"🗼 𝗣𝗜𝗦𝗢 {piso}\n\n"
        f"{monstruo['emoji']} 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['nombre']}\n"
        f"❤️ 𝗩𝗜𝗗𝗔 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['vida']}\n\n"
        f"❤️ 𝗧𝗨 𝗩𝗜𝗗𝗔: {partida['vida']}\n"
        f"⚔️ 𝗧𝗨 𝗗𝗔Ñ𝗢: {partida['arma_daño']}\n"
        f"💊 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦: {partida['pociones']}",
        reply_markup=markup
    )

# ---------- ACCIONES DE BATALLA ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("accion_"))
def accion_batalla(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if user_id not in progreso or "partida" not in progreso[user_id]:
        bot.send_message(chat_id, "❌ 𝗡𝗢 𝗛𝗔𝗬 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗔𝗖𝗧𝗜𝗩𝗔")
        return

    partida = progreso[user_id]["partida"]
    monstruo = partida["monstruo_actual"]
    if monstruo is None:
        bot.send_message(chat_id, "❌ 𝗡𝗢 𝗛𝗔𝗬 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗔𝗖𝗧𝗜𝗩𝗔")
        return

    accion = call.data

    if accion == "accion_atacar":
        daño = partida["arma_daño"]
        monstruo["vida"] -= daño
        daño_recibido = monstruo["daño"]
        partida["vida"] -= daño_recibido
        resultado = "⚔️ 𝗔𝗧𝗔𝗖𝗔𝗦𝗧𝗘 𝗔𝗟 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢"

    elif accion == "accion_defender":
        daño_recibido = monstruo["daño"] // 2
        partida["vida"] -= daño_recibido
        resultado = "🛡️ 𝗧𝗘 𝗗𝗘𝗙𝗘𝗡𝗗𝗜𝗦𝗧𝗘"

    elif accion == "accion_magia":
        if random.random() < 0.7:
            daño = partida["arma_daño"] * 3
            monstruo["vida"] -= daño
            daño_recibido = monstruo["daño"]
            partida["vida"] -= daño_recibido
            resultado = "✨ 𝗟𝗔 𝗠𝗔𝗚𝗜𝗔 𝗙𝗨𝗘 𝗘𝗫𝗜𝗧𝗢𝗦𝗔"
        else:
            daño_recibido = monstruo["daño"] * 2
            partida["vida"] -= daño_recibido
            resultado = "❌ 𝗟𝗔 𝗠𝗔𝗚𝗜𝗔 𝗙𝗔𝗟𝗟𝗢"

    elif accion == "accion_pocion":
        if partida["pociones"] > 0:
            partida["pociones"] -= 1
            partida["vida"] += 50
            if partida["vida"] > 100:
                partida["vida"] = 100
            resultado = "💊 𝗥𝗘𝗖𝗨𝗣𝗘𝗥𝗔𝗦𝗧𝗘 𝟱𝟬 𝗗𝗘 𝗩𝗜𝗗𝗔"
        else:
            resultado = "❌ 𝗡𝗢 𝗧𝗜𝗘𝗡𝗘𝗦 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦"

    # Guardar cambios
    guardar_progreso()

    if partida["vida"] <= 0:
        bot.send_message(chat_id,
            "💀 𝗖𝗔𝗜𝗦𝗧𝗘\n\n"
            f"Moriste en el piso {partida['piso']}.\n"
            f"Experiencia ganada: {partida['piso'] * 2}"
        )
        progreso[user_id]["piso_maximo"] = max(progreso[user_id]["piso_maximo"], partida["piso"])
        progreso[user_id]["experiencia"] += partida["piso"] * 2
        # Limpiar partida activa
        progreso[user_id].pop("partida", None)
        guardar_progreso()
        return

    if monstruo["vida"] <= 0:
        oro_ganado = monstruo["oro"]
        xp_ganada = monstruo["xp"]
        progreso[user_id]["oro"] += oro_ganado
        progreso[user_id]["experiencia"] += xp_ganada
        partida["piso"] += 1
        partida["vida"] = min(partida["vida"] + 10, 100)  # Pequeña regeneración al subir de piso
        progreso[user_id]["piso_actual"] = partida["piso"]
        guardar_progreso()

        bot.send_message(chat_id,
            f"✅ 𝗩𝗘𝗡𝗖𝗜𝗦𝗧𝗘 𝗔𝗟 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢\n\n"
            f"🪙 𝗢𝗥𝗢 𝗚𝗔𝗡𝗔𝗗𝗢: {oro_ganado}\n"
            f"⭐ 𝗘𝗫𝗣: {xp_ganada}\n\n"
            f"🗼 𝗦𝗨𝗕𝗘𝗦 𝗔𝗟 𝗣𝗜𝗦𝗢 {partida['piso']}"
        )
        mostrar_piso(call.message, user_id)
        return

    bot.send_message(chat_id,
        f"{resultado}\n\n"
        f"❤️ 𝗧𝗨 𝗩𝗜𝗗𝗔: {partida['vida']}\n"
        f"❤️ 𝗩𝗜𝗗𝗔 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['vida']}"
    )
    mostrar_piso(call.message, user_id)

# ---------- COMANDO /miprogreso ----------
@bot.message_handler(commands=['miprogreso'])
def mi_progreso(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ 𝗘𝗦𝗧𝗘 𝗖𝗢𝗠𝗔𝗡𝗗𝗢 𝗦𝗢𝗟𝗢 𝗙𝗨𝗡𝗖𝗜𝗢𝗡𝗔 𝗘𝗡 𝗚𝗥𝗨𝗣𝗢𝗦")
        return

    user_id = message.from_user.id
    if user_id not in progreso:
        bot.reply_to(message, "❌ 𝗔𝗨𝗡 𝗡𝗢 𝗛𝗔𝗦 𝗝𝗨𝗚𝗔𝗗𝗢")
        return

    p = progreso[user_id]
    bot.reply_to(message,
        f"📊 𝗧𝗨 𝗣𝗥𝗢𝗚𝗥𝗘𝗦𝗢\n\n"
        f"👤 𝗡𝗢𝗠𝗕𝗥𝗘: {p['nombre']}\n"
        f"🗼 𝗣𝗜𝗦𝗢 𝗠𝗔𝗫𝗜𝗠𝗢: {p['piso_maximo']}\n"
        f"🪙 𝗢𝗥𝗢: {p['oro']}\n"
        f"⭐ 𝗘𝗫𝗣𝗘𝗥𝗜𝗘𝗡𝗖𝗜𝗔: {p['experiencia']}"
    )

# ---------- COMANDO /rank ----------
@bot.message_handler(commands=['rank'])
def ranking(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "❌ 𝗘𝗦𝗧𝗘 𝗖𝗢𝗠𝗔𝗡𝗗𝗢 𝗦𝗢𝗟𝗢 𝗙𝗨𝗡𝗖𝗜𝗢𝗡𝗔 𝗘𝗡 𝗚𝗥𝗨𝗣𝗢𝗦")
        return

    if not progreso:
        bot.reply_to(message, "📊 𝗔𝗨𝗡 𝗡𝗢 𝗛𝗔𝗬 𝗝𝗨𝗚𝗔𝗗𝗢𝗥𝗘𝗦")
        return

    ranking = sorted(progreso.items(), key=lambda x: x[1]["piso_maximo"], reverse=True)

    texto = "🏆 𝗥𝗔𝗡𝗞𝗜𝗡𝗚 𝗗𝗘 𝗟𝗔 𝗧𝗢𝗥𝗥𝗘\n\n"
    for i, (user_id, datos) in enumerate(ranking[:10], 1):
        texto += f"{i}. {datos['nombre']} - Piso {datos['piso_maximo']}\n"

    bot.reply_to(message, texto)

# ---------- INICIAR BOT ----------
def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
