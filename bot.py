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
BASE_URL = "https://raw.githubusercontent.com/Home-CentralCommand/la-torre-infinita-bot/main/monstruos"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ---------- PERSISTENCIA EN GITHUB ----------
def github_get(file_path):
    if not GITHUB_TOKEN: return None
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
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
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except:
        pass
    encoded = base64.b64encode(content.encode()).decode()
    body = {"message": f"Update {file_path}", "content": encoded}
    if sha:
        body["sha"] = sha
    try:
        requests.put(url, headers=headers, json=body, timeout=5)
    except:
        pass

def cargar_progreso():
    data = github_get(FILE_PATH_PROGRESS)
    if data:
        try:
            return json.loads(data)
        except:
            pass
    return {}

def guardar_progreso():
    try:
        github_put(FILE_PATH_PROGRESS, json.dumps(progreso, indent=2))
    except:
        pass

# ---------- DATOS DEL JUEGO ----------
monstruos = [
    {
        "nombre": "Alma Errante",
        "emoji": "🧟",
        "vida": 20,
        "daño": 5,
        "oro": 10,
        "xp": 5,
        "imagen": "alma_errante.jpg",
        "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗔𝗦 𝗔𝗟𝗠𝗔𝗦",
        "zona": "Cementerio Olvidado",
        "descripcion": "𝘜𝘯 𝘦𝘴𝘱𝘦𝘤𝘵𝘳𝘰 𝘲𝘶𝘦 𝘥𝘦𝘢𝘮𝘣𝘶𝘭𝘢 𝘦𝘵𝘦𝘳𝘯𝘢𝘮𝘦𝘯𝘵𝘦.\n𝘚𝘶𝘴 𝘨𝘦𝘮𝘪𝘥𝘰𝘴 𝘩𝘪𝘦𝘭𝘢𝘯 𝘭𝘢 𝘴𝘢𝘯𝘨𝘳𝘦."
    },
    {
        "nombre": "Orco Salvaje",
        "emoji": "🧌",
        "vida": 30,
        "daño": 8,
        "oro": 15,
        "xp": 8,
        "imagen": "orco_salvaje.jpg",
        "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗔 𝗛𝗢𝗥𝗗𝗔",
        "zona": "La Horda",
        "descripcion": "𝘜𝘯𝘢 𝘣𝘦𝘴𝘵𝘪𝘢 𝘮𝘶𝘴𝘤𝘶𝘭𝘰𝘴𝘢 𝘤𝘰𝘯 𝘴𝘦𝘥 𝘥𝘦 𝘴𝘢𝘯𝘨𝘳𝘦.\n𝘚𝘶 𝘩𝘢𝘤𝘩𝘢 𝘦𝘴 𝘵𝘢𝘯 𝘨𝘳𝘢𝘯𝘥𝘦 𝘤𝘰𝘮𝘰 𝘴𝘶 𝘧𝘶𝘳𝘪𝘢."
    },
    {
        "nombre": "Demonio Menor",
        "emoji": "👹",
        "vida": 40,
        "daño": 12,
        "oro": 20,
        "xp": 12,
        "imagen": "demonio_menor.jpg",
        "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗢𝗦 𝗗𝗘𝗠𝗢𝗡𝗜𝗢𝗦",
        "zona": "El Infierno",
        "descripcion": "𝘜𝘯 𝘴𝘦𝘳 𝘥𝘦 𝘭𝘭𝘢𝘮𝘢𝘴 𝘺 𝘤𝘰𝘭𝘦𝘳𝘢.\n𝘚𝘶𝘴 𝘤𝘶𝘦𝘳𝘯𝘰𝘴 𝘣𝘳𝘪𝘭𝘭𝘢𝘯 𝘦𝘯 𝘭𝘢 𝘰𝘴𝘤𝘶𝘳𝘪𝘥𝘢𝘥."
    },
    {
        "nombre": "Wyrm Sombrío",
        "emoji": "🐉",
        "vida": 55,
        "daño": 15,
        "oro": 30,
        "xp": 15,
        "imagen": "wyrm_sombrio.jpg",
        "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗔𝗦 𝗦𝗢𝗠𝗕𝗥𝗔𝗦",
        "zona": "Las Sombras",
        "descripcion": "𝘜𝘯 𝘥𝘳𝘢𝘨𝘰𝘯 𝘥𝘦 𝘦𝘴𝘤𝘢𝘮𝘢𝘴 𝘰𝘴𝘤𝘶𝘳𝘢𝘴.\n𝘚𝘶 𝘢𝘭𝘪𝘦𝘯𝘵𝘰 𝘦𝘴 𝘷𝘦𝘯𝘦𝘯𝘰 𝘱𝘶𝘳𝘰."
    },
    {
        "nombre": "Caballero Caído",
        "emoji": "⚔️",
        "vida": 70,
        "daño": 18,
        "oro": 40,
        "xp": 18,
        "imagen": "caballero_caido.jpg",
        "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗔 𝗚𝗨𝗘𝗥𝗥𝗔",
        "zona": "La Guerra",
        "descripcion": "𝘜𝘯 𝘨𝘶𝘦𝘳𝘳𝘦𝘳𝘰 𝘤𝘰𝘳𝘳𝘰𝘮𝘱𝘪𝘥𝘰 𝘱𝘰𝘳 𝘭𝘢 𝘰𝘴𝘤𝘶𝘳𝘪𝘥𝘢𝘥.\n𝘚𝘶 𝘦𝘴𝘱𝘢𝘥𝘢 𝘢𝘶́𝘯 𝘳𝘦𝘤𝘶𝘦𝘳𝘥𝘢 𝘭𝘢 𝘨𝘭𝘰𝘳𝘪𝘢."
    },
    {
        "nombre": "Liche Maligno",
        "emoji": "🪄",
        "vida": 90,
        "daño": 22,
        "oro": 55,
        "xp": 22,
        "imagen": "liche_maligno.jpg",
        "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗔 𝗠𝗔𝗚𝗜𝗔 𝗢𝗦𝗖𝗨𝗥𝗔",
        "zona": "La Magia Oscura",
        "descripcion": "𝘜𝘯 𝘯𝘪𝘨𝘳𝘰𝘮𝘢𝘯𝘵𝘦 𝘲𝘶𝘦 𝘥𝘦𝘴𝘢𝘧𝘪́𝘢 𝘢 𝘭𝘢 𝘮𝘶𝘦𝘳𝘵𝘦.\n𝘚𝘶 𝘮𝘢𝘨𝘪𝘢 𝘤𝘰𝘳𝘳𝘰𝘮𝘱𝘦 𝘦𝘭 𝘢𝘭𝘮𝘢."
    },
]

jefes = [
    {
        "nombre": "Señor de las Sombras",
        "emoji": "👑",
        "vida": 120,
        "daño": 25,
        "oro": 80,
        "xp": 35,
        "imagen": "senor_de_las_sombras.jpg",
        "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗔 𝗢𝗦𝗖𝗨𝗥𝗜𝗗𝗔𝗗 𝗘𝗧𝗘𝗥𝗡𝗔",
        "zona": "La Oscuridad Eterna",
        "descripcion": "𝘌𝘭 𝘳𝘦𝘺 𝘥𝘦 𝘭𝘢𝘴 𝘴𝘰𝘮𝘣𝘳𝘢𝘴 𝘩𝘢 𝘥𝘦𝘴𝘱𝘦𝘳𝘵𝘢𝘥𝘰.\n𝘚𝘶 𝘱𝘰𝘥𝘦𝘳 𝘩𝘢𝘤𝘦 𝘵𝘦𝘮𝘣𝘭𝘢𝘳 𝘢 𝘭𝘰𝘴 𝘷𝘢𝘭𝘪𝘦𝘯𝘵𝘦𝘴."
    },
]

# ---------- INICIALIZACIÓN ----------
progreso = cargar_progreso()
partidas = {}

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
        }
        guardar_progreso()

    partidas[user_id] = {
        "vida": 100,
        "piso": 1,
        "arma_daño": progreso[user_id].get("arma_daño", 10),
        "pociones": progreso[user_id].get("pociones", 1),
        "monstruo_actual": None,
        "message_id": None
    }

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚔️ 𝗖𝗢𝗠𝗘𝗡𝗭𝗔𝗥", callback_data="iniciar_aventura"),
        InlineKeyboardButton("📜 𝗚𝗨𝗜𝗔", callback_data="ver_guia")
    )

    bot.send_message(chat_id,
        "🗼 𝗟𝗔 𝗧𝗢𝗥𝗥𝗘 𝗜𝗡𝗙𝗜𝗡𝗜𝗧𝗔\n\n"
        "⚔️ 𝗥𝗣𝗚 𝗱𝗲 𝗮𝘃𝗲𝗻𝘁𝘂𝗿𝗮 𝗼𝘀𝗰𝘂𝗿𝗮.\n"
        "Sube pisos, vence monstruos y haz historia.\n\n"
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
        "Daño masivo, pero puede fallar.\n"
        "60% de probabilidad de éxito.\n\n"
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

    if user_id not in partidas:
        bot.send_message(call.message.chat.id, "❌ 𝗡𝗢 𝗛𝗔𝗬 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗔𝗖𝗧𝗜𝗩𝗔")
        return

    mostrar_nuevo_piso(call.message.chat.id, user_id)

def mostrar_nuevo_piso(chat_id, user_id):
    if user_id not in partidas:
        return

    try:
        if partidas[user_id].get("message_id"):
            bot.delete_message(chat_id, partidas[user_id]["message_id"])
    except:
        pass

    partida = partidas[user_id]

    if not partida.get("monstruo_actual") or partida["monstruo_actual"]["vida"] <= 0:
        piso = partida["piso"]
        if piso % 10 == 0:
            monstruo = jefes[0].copy()
        else:
            monstruo = random.choice(monstruos).copy()
        partida["monstruo_actual"] = monstruo
    else:
        monstruo = partida["monstruo_actual"]

    piso = partida["piso"]
    imagen_url = f"{BASE_URL}/{monstruo['imagen']}"

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚔️ 𝗔𝗧𝗔𝗖𝗔𝗥", callback_data="accion_atacar"),
        InlineKeyboardButton("🛡️ 𝗗𝗘𝗙𝗘𝗡𝗗𝗘𝗥", callback_data="accion_defender"),
        InlineKeyboardButton("✨ 𝗠𝗔𝗚𝗜𝗔\n𝘔𝘢𝘨𝘪𝘤 𝘢𝘵𝘵𝘢𝘤𝘬 - %60 𝘤𝘩𝘢𝘯𝘤𝘦", callback_data="accion_magia"),
        InlineKeyboardButton("💊 𝗣𝗢𝗖𝗜𝗢𝗡", callback_data="accion_pocion")
    )

    texto = (
        f"🗼 𝗣𝗜𝗦𝗢 {piso} - {monstruo['zona']}\n"
        f"{monstruo['mundo']}\n\n"
        f"{monstruo['descripcion']}\n\n"
        f"{monstruo['emoji']} 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['nombre']}\n"
        f"❤️ 𝗩𝗜𝗗𝗔 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['vida']}\n\n"
        f"❤️ 𝗧𝗨 𝗩𝗜𝗗𝗔: {partida['vida']}\n"
        f"⚔️ 𝗣𝗢𝗗𝗘𝗥 𝗗𝗘 𝗔𝗧𝗔𝗤𝗨𝗘: {partida['arma_daño']}\n"
        f"💊 𝗧𝗨𝗦 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦: {partida['pociones']}\n\n"
        "¿𝗤𝘂𝗲́ 𝗱𝗲𝘀𝗲𝗮𝘀 𝗵𝗮𝗰𝗲𝗿?"
    )

    try:
        msg = bot.send_photo(
            chat_id,
            photo=imagen_url,
            caption=texto,
            reply_markup=markup
        )
        partida["message_id"] = msg.message_id
    except:
        msg = bot.send_message(chat_id, texto, reply_markup=markup)
        partida["message_id"] = msg.message_id

# ---------- ACCIONES DE BATALLA ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("accion_"))
def accion_batalla(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if user_id not in partidas:
        bot.send_message(chat_id, "❌ 𝗡𝗢 𝗛𝗔𝗬 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗔𝗖𝗧𝗜𝗩𝗔")
        return

    partida = partidas[user_id]
    monstruo = partida.get("monstruo_actual")
    if monstruo is None:
        bot.send_message(chat_id, "❌ 𝗡𝗢 𝗛𝗔𝗬 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗔𝗖𝗧𝗜𝗩𝗔")
        return

    accion = call.data
    resultado = ""

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

    if partida["vida"] <= 0:
        exp_ganada = partida["piso"] * 2
        progreso[user_id]["experiencia"] += exp_ganada
        progreso[user_id]["piso_maximo"] = max(progreso[user_id].get("piso_maximo", 0), partida["piso"])
        guardar_progreso()

        bot.send_message(chat_id,
            "💀 𝗛𝗔𝗦 𝗖𝗔𝗜𝗗𝗢 𝗘𝗡 𝗕𝗔𝗧𝗔𝗟𝗟𝗔\n\n"
            f"{monstruo['emoji']} {monstruo['nombre']} te ha derrotado en el piso {partida['piso']}.\n\n"
            f"⭐ Experiencia ganada: {exp_ganada}\n"
            f"🪙 Oro acumulado: {progreso[user_id].get('oro', 0)}\n"
            f"🗼 Piso máximo alcanzado: {progreso[user_id]['piso_maximo']}\n\n"
            "La torre te espera de nuevo.\n"
            "Escribe /torre para volver a intentarlo.\n\n"
            "“No es el fin, solo una pausa en tu leyenda.”"
        )
        partidas.pop(user_id, None)
        return

    if monstruo["vida"] <= 0:
        oro_ganado = monstruo["oro"]
        xp_ganada = monstruo["xp"]
        progreso[user_id]["oro"] += oro_ganado
        progreso[user_id]["experiencia"] += xp_ganada
        partida["piso"] += 1
        partida["vida"] = min(partida["vida"] + 10, 100)
        progreso[user_id]["piso_actual"] = partida["piso"]
        partida["monstruo_actual"] = None
        guardar_progreso()

        bot.send_message(chat_id,
            "⚔️ 𝗩𝗜𝗖𝗧𝗢𝗥𝗜𝗔\n\n"
            "Has derrotado a:\n"
            f"{monstruo['emoji']} {monstruo['nombre']}.\n\n"
            f"🪙 𝗢𝗥𝗢 𝗚𝗔𝗡𝗔𝗗𝗢: {oro_ganado}\n"
            f"⭐ 𝗘𝗫𝗣𝗘𝗥𝗜𝗘𝗡𝗖𝗜𝗔: {xp_ganada}\n"
            "❤️ 𝗩𝗜𝗗𝗔 𝗥𝗘𝗖𝗨𝗣𝗘𝗥𝗔𝗗𝗔: +10\n\n"
            f"🗼 𝗣𝗜𝗦𝗢 𝗔𝗟𝗖𝗔𝗡𝗭𝗔𝗗𝗢: {partida['piso']}\n\n"
            "⏳ El siguiente monstruo aparecerá en 5 segundos..."
        )
        threading.Timer(5, lambda: mostrar_nuevo_piso(chat_id, user_id)).start()
        return

    nuevo_texto = (
        f"{resultado}\n\n"
        f"{monstruo['emoji']} 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['nombre']}\n"
        f"❤️ 𝗩𝗜𝗗𝗔 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['vida']}\n\n"
        f"❤️ 𝗧𝗨 𝗩𝗜𝗗𝗔: {partida['vida']}\n"
        f"⚔️ 𝗣𝗢𝗗𝗘𝗥 𝗗𝗘 𝗔𝗧𝗔𝗤𝗨𝗘: {partida['arma_daño']}\n"
        f"💊 𝗧𝗨𝗦 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦: {partida['pociones']}\n\n"
        "¿𝗤𝘂𝗲́ 𝗱𝗲𝘀𝗲𝗮𝘀 𝗵𝗮𝗰𝗲𝗿?"
    )

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚔️ 𝗔𝗧𝗔𝗖𝗔𝗥", callback_data="accion_atacar"),
        InlineKeyboardButton("🛡️ 𝗗𝗘𝗙𝗘𝗡𝗗𝗘𝗥", callback_data="accion_defender"),
        InlineKeyboardButton("✨ 𝗠𝗔𝗚𝗜𝗔\n𝘔𝘢𝘨𝘪𝘤 𝘢𝘵𝘵𝘢𝘤𝘬 - %60 𝘤𝘩𝘢𝘯𝘤𝘦", callback_data="accion_magia"),
        InlineKeyboardButton("💊 𝗣𝗢𝗖𝗜𝗢𝗡", callback_data="accion_pocion")
    )

    try:
        bot.edit_message_caption(
            chat_id=chat_id,
            message_id=partida["message_id"],
            caption=nuevo_texto,
            reply_markup=markup
        )
    except:
        msg = bot.send_message(chat_id, nuevo_texto, reply_markup=markup)
        partida["message_id"] = msg.message_id

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
        f"🗼 𝗣𝗜𝗦𝗢 𝗠𝗔𝗫𝗜𝗠𝗢: {p.get('piso_maximo', 0)}\n"
        f"🪙 𝗢𝗥𝗢: {p.get('oro', 0)}\n"
        f"⭐ 𝗘𝗫𝗣𝗘𝗥𝗜𝗘𝗡𝗖𝗜𝗔: {p.get('experiencia', 0)}"
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

    ranking = sorted(progreso.items(), key=lambda x: x[1].get("piso_maximo", 0), reverse=True)

    texto = "🏆 𝗥𝗔𝗡𝗞𝗜𝗡𝗚 𝗗𝗘 𝗟𝗔 𝗧𝗢𝗥𝗥𝗘\n\n"
    for i, (user_id, datos) in enumerate(ranking[:10], 1):
        texto += f"{i}. {datos['nombre']} - Piso {datos.get('piso_maximo', 0)}\n"

    bot.reply_to(message, texto)

# ---------- INICIAR BOT ----------
def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
