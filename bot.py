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
import logging

TOKEN = "8900609729:AAHiqL3g7eRVbZtDE-wLg9sGEUfATe7RwNo"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "Home-CentralCommand/la-torre-infinita-bot"
FILE_PATH_PROGRESS = "progreso.json"
BASE_URL = "https://raw.githubusercontent.com/Home-CentralCommand/la-torre-infinita-bot/main/monstruos"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Cache de imágenes con límite
imagenes_cache = {}
MAX_CACHE_SIZE = 50

# ---------- PERSISTENCIA EN GITHUB ----------
def github_get(file_path):
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN no configurado")
        return None
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            content = base64.b64decode(r.json()["content"]).decode()
            return content
        else:
            logger.error(f"Error en github_get: {r.status_code}")
            return None
    except Exception as e:
        logger.error(f"Excepción en github_get: {e}")
        return None

def github_put(file_path, content, retries=3):
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN no configurado")
        return False
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    sha = None
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except:
        pass
    encoded = base64.b64encode(content.encode()).decode()
    body = {"message": f"Update {file_path}", "content": encoded}
    if sha:
        body["sha"] = sha
    for intento in range(retries):
        try:
            r = requests.put(url, headers=headers, json=body, timeout=10)
            if r.status_code in [200, 201]:
                return True
            else:
                logger.error(f"Error en github_put (intento {intento+1}): {r.status_code}")
        except Exception as e:
            logger.error(f"Excepción en github_put (intento {intento+1}): {e}")
        time.sleep(2)
    return False

def cargar_progreso():
    data = github_get(FILE_PATH_PROGRESS)
    if data:
        try:
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error parseando progreso: {e}")
    return {}

def guardar_progreso():
    try:
        return github_put(FILE_PATH_PROGRESS, json.dumps(progreso, indent=2))
    except Exception as e:
        logger.error(f"Error en guardar_progreso: {e}")
        return False

# ---------- DATOS DEL JUEGO ----------
monstruos_base = [
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

jefe_normal = {
    "nombre": "Guardián de la Torre",
    "emoji": "🗿",
    "vida": 100,
    "daño": 20,
    "oro": 60,
    "xp": 25,
    "imagen": "guardian_de_la_torre.jpg",
    "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗢𝗦 𝗚𝗨𝗔𝗥𝗗𝗜𝗔𝗡𝗘𝗦",
    "zona": "La Fortaleza",
    "descripcion": "𝘜𝘯 𝘨𝘰𝘭𝘦𝘮 𝘢𝘯𝘤𝘦𝘴𝘵𝘳𝘢𝘭 𝘲𝘶𝘦 𝘱𝘳𝘰𝘵𝘦𝘨𝘦 𝘭𝘢 𝘵𝘰𝘳𝘳𝘦.\n𝘚𝘶 𝘱𝘪𝘦𝘭 𝘥𝘦 𝘱𝘪𝘦𝘥𝘳𝘢 𝘦𝘴 𝘤𝘢𝘴𝘪 𝘪𝘮𝘱𝘦𝘯𝘦𝘵𝘳𝘢𝘣𝘭𝘦."
}

jefe_final = {
    "nombre": "Señor de las Sombras",
    "emoji": "👑",
    "vida": 150,
    "daño": 30,
    "oro": 100,
    "xp": 50,
    "imagen": "senor_de_las_sombras.jpg",
    "mundo": "𝗘𝗟 𝗠𝗨𝗡𝗗𝗢 𝗗𝗘 𝗟𝗔 𝗢𝗦𝗖𝗨𝗥𝗜𝗗𝗔𝗗 𝗘𝗧𝗘𝗥𝗡𝗔",
    "zona": "La Oscuridad Eterna",
    "descripcion": "𝘌𝘭 𝘳𝘦𝘺 𝘥𝘦 𝘭𝘢𝘴 𝘴𝘰𝘮𝘣𝘳𝘢𝘴 𝘩𝘢 𝘥𝘦𝘴𝘱𝘦𝘳𝘵𝘢𝘥𝘰.\n𝘚𝘶 𝘱𝘰𝘥𝘦𝘳 𝘩𝘢𝘤𝘦 𝘵𝘦𝘮𝘣𝘭𝘢𝘳 𝘢 𝘭𝘰𝘴 𝘷𝘢𝘭𝘪𝘦𝘯𝘵𝘦𝘴."
}

# ---------- INICIALIZACIÓN ----------
progreso = cargar_progreso()
partidas = {}

# ---------- LIMPIEZA DE PARTIDAS ----------
def limpiar_partidas():
    while True:
        ahora = time.time()
        for user_id in list(partidas.keys()):
            if ahora - partidas[user_id].get("ultimo_acceso", ahora) > 3600:
                partidas.pop(user_id, None)
                logger.info(f"Partida de {user_id} eliminada por inactividad")
        time.sleep(600)

threading.Thread(target=limpiar_partidas, daemon=True).start()

# ---------- RUTA FLASK ----------
@app.route('/')
def home():
    return "Bot running"

# ---------- COMANDO /start ----------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "🗼 𝗟𝗔 𝗧𝗢𝗥𝗥𝗘 𝗜𝗡𝗙𝗜𝗡𝗜𝗧𝗔\n\n"
        "⚔️ 𝗥𝗣𝗚 𝗱𝗲 𝗮𝘃𝗲𝗻𝘁𝘂𝗿𝗮 𝗼𝘀𝗰𝘂𝗿𝗮.\n\n"
        "Comandos:\n"
        "▸ /torre - Iniciar aventura\n"
        "▸ /miprogreso - Ver progreso\n"
        "▸ /rank - Ranking\n"
        "▸ /cancel - Salir de partida\n\n"
        "Escribe /torre para comenzar."
    )

# ---------- COMANDO /cancel ----------
@bot.message_handler(commands=['cancel'])
def cancelar_partida(message):
    user_id = message.from_user.id
    if user_id in partidas:
        # Guardar oro acumulado
        oro_ganado = partidas[user_id].get("oro_ganado", 0)
        if oro_ganado > 0:
            progreso[user_id]["oro"] = progreso[user_id].get("oro", 0) + oro_ganado
            guardar_progreso()
        partidas.pop(user_id, None)
        bot.reply_to(message, "✅ 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗖𝗔𝗡𝗖𝗘𝗟𝗔𝗗𝗔\n\nTu oro ganado fue guardado.")
    else:
        bot.reply_to(message, "❌ 𝗡𝗢 𝗧𝗜𝗘𝗡𝗘𝗦 𝗣𝗔𝗥𝗧𝗜𝗗𝗔 𝗔𝗖𝗧𝗜𝗩𝗔")

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
        "message_id": None,
        "oro_ganado": 0,
        "ultimo_acceso": time.time(),
        "procesando": False,
        "acciones_sin_guardar": 0
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
        "▸ /rank - Ranking\n"
        "▸ /cancel - Cancelar partida"
    )

# ---------- INICIAR AVENTURA ----------
@bot.callback_query_handler(func=lambda call: call.data == "iniciar_aventura")
def iniciar_aventura(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    if user_id not in partidas:
        return

    partidas[user_id]["ultimo_acceso"] = time.time()
    mostrar_nuevo_piso(call.message.chat.id, user_id)

def obtener_monstruo_escalado(piso):
    """Genera un monstruo con estadísticas escaladas según el piso"""
    if piso % 10 == 0:
        base = jefe_final.copy()
    elif piso % 5 == 0:
        base = jefe_normal.copy()
    else:
        base = random.choice(monstruos_base).copy()
    
    # Factor de escalado: 10% más difícil por piso
    factor = 1 + (piso - 1) * 0.1
    base["vida"] = max(1, int(base["vida"] * factor))
    base["daño"] = max(1, int(base["daño"] * factor))
    base["oro"] = max(1, int(base["oro"] * factor))
    base["xp"] = max(1, int(base["xp"] * factor))
    
    return base

def mostrar_nuevo_piso(chat_id, user_id):
    if user_id not in partidas:
        return

    partida = partidas[user_id]
    partida["ultimo_acceso"] = time.time()

    # Limpiar mensaje anterior
    try:
        if partida.get("message_id"):
            bot.delete_message(chat_id, partida["message_id"])
    except:
        pass
    finally:
        partida["message_id"] = None

    # Generar monstruo solo si no hay o está muerto
    if not partida.get("monstruo_actual") or partida["monstruo_actual"]["vida"] <= 0:
        partida["monstruo_actual"] = obtener_monstruo_escalado(partida["piso"])
    else:
        monstruo = partida["monstruo_actual"]

    monstruo = partida["monstruo_actual"]
    piso = partida["piso"]
    imagen_url = f"{BASE_URL}/{monstruo['imagen']}"

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚔️ 𝗔𝗧𝗔𝗖𝗔𝗥", callback_data="accion_atacar"),
        InlineKeyboardButton("🛡️ 𝗗𝗘𝗙𝗘𝗡𝗗𝗘𝗥", callback_data="accion_defender"),
        InlineKeyboardButton("✨ 𝗠𝗔𝗚𝗜𝗔 - 𝘔𝘢𝘨𝘪𝘤 𝘢𝘵𝘵𝘢𝘤𝘬 %60", callback_data="accion_magia"),
        InlineKeyboardButton("💊 𝗣𝗢𝗖𝗜𝗢𝗡 - 𝘊𝘢𝘳𝘨𝘢𝘳 𝘷𝘪𝘥𝘢 +50", callback_data="accion_pocion"),
        InlineKeyboardButton("🛒 𝗧𝗜𝗘𝗡𝗗𝗔", callback_data="abrir_tienda")
    )

    texto = (
        f"🗼 𝗣𝗜𝗦𝗢 {piso} - {monstruo['zona']}\n"
        f"{monstruo['mundo']}\n\n"
        f"{monstruo['descripcion']}\n\n"
        f"{monstruo['emoji']} 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['nombre']}\n"
        f"❤️ 𝗩𝗜𝗗𝗔 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['vida']}\n"
        f"⚔️ 𝗗𝗔Ñ𝗢 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['daño']}\n\n"
        f"❤️ 𝗧𝗨 𝗩𝗜𝗗𝗔: {partida['vida']}\n"
        f"⚔️ 𝗣𝗢𝗗𝗘𝗥 𝗗𝗘 𝗔𝗧𝗔𝗤𝗨𝗘: {partida['arma_daño']}\n"
        f"💊 𝗧𝗨𝗦 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦: {partida['pociones']}\n"
        f"🪙 𝗧𝗨 𝗢𝗥𝗢: {progreso[user_id].get('oro', 0)}\n\n"
        "¿𝗤𝘂𝗲́ 𝗱𝗲𝘀𝗲𝗮𝘀 𝗵𝗮𝗰𝗲𝗿?"
    )

    # Usar caché de imágenes con validación
    if imagen_url not in imagenes_cache:
        try:
            r = requests.get(imagen_url, timeout=10)
            if r.status_code == 200:
                if len(imagenes_cache) >= MAX_CACHE_SIZE:
                    # Eliminar entrada más antigua
                    primera_clave = next(iter(imagenes_cache))
                    del imagenes_cache[primera_clave]
                imagenes_cache[imagen_url] = r.content
            else:
                imagenes_cache[imagen_url] = None
                logger.error(f"Imagen no encontrada: {imagen_url} (status {r.status_code})")
        except Exception as e:
            imagenes_cache[imagen_url] = None
            logger.error(f"Error descargando imagen {imagen_url}: {e}")

    try:
        if imagenes_cache.get(imagen_url):
            msg = bot.send_photo(
                chat_id,
                photo=imagenes_cache[imagen_url],
                caption=texto,
                reply_markup=markup
            )
        else:
            msg = bot.send_message(chat_id, texto, reply_markup=markup)
        partida["message_id"] = msg.message_id
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        try:
            msg = bot.send_message(chat_id, texto, reply_markup=markup)
            partida["message_id"] = msg.message_id
        except:
            pass

# ---------- TIENDA ----------
@bot.callback_query_handler(func=lambda call: call.data == "abrir_tienda")
def abrir_tienda(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    if user_id not in partidas:
        return

    if partidas[user_id].get("procesando"):
        return

    partidas[user_id]["ultimo_acceso"] = time.time()

    # Borrar mensaje de batalla anterior
    try:
        if partidas[user_id].get("message_id"):
            bot.delete_message(call.message.chat.id, partidas[user_id]["message_id"])
            partidas[user_id]["message_id"] = None
    except:
        pass

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("💊 Comprar Poción - 20 oro", callback_data="comprar_pocion"),
        InlineKeyboardButton("⬅️ Volver", callback_data="volver_batalla")
    )

    try:
        bot.send_message(call.message.chat.id,
            "🛒 𝗧𝗜𝗘𝗡𝗗𝗔 𝗗𝗘 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦\n\n"
            f"🪙 Tu oro: {progreso[user_id].get('oro', 0)}\n"
            "💊 Poción de vida +50\n"
            "💰 Costo: 20 de oro\n\n"
            "¿Qué deseas hacer?",
            reply_markup=markup
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "comprar_pocion")
def comprar_pocion(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    if user_id not in partidas:
        return

    if partidas[user_id].get("procesando"):
        return

    partidas[user_id]["ultimo_acceso"] = time.time()
    oro = progreso[user_id].get("oro", 0)

    if oro >= 20:
        progreso[user_id]["oro"] = oro - 20
        partidas[user_id]["pociones"] = partidas[user_id].get("pociones", 0) + 1
        partidas[user_id]["acciones_sin_guardar"] += 1
        if partidas[user_id]["acciones_sin_guardar"] >= 10:
            guardar_progreso()
            partidas[user_id]["acciones_sin_guardar"] = 0
        try:
            bot.send_message(call.message.chat.id,
                "✅ 𝗖𝗢𝗠𝗣𝗥𝗔 𝗘𝗫𝗜𝗧𝗢𝗦𝗔\n\n"
                "💊 Poción agregada a tu inventario.\n"
                f"🪙 Oro restante: {progreso[user_id]['oro']}"
            )
        except:
            pass
    else:
        try:
            bot.send_message(call.message.chat.id,
                "❌ 𝗢𝗥𝗢 𝗜𝗡𝗦𝗨𝗙𝗜𝗖𝗜𝗘𝗡𝗧𝗘\n\n"
                "Necesitas 20 de oro para comprar."
            )
        except:
            pass

    # Borrar mensaje de tienda
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    mostrar_nuevo_piso(call.message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "volver_batalla")
def volver_batalla(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    if user_id not in partidas:
        return

    partidas[user_id]["ultimo_acceso"] = time.time()

    # Borrar mensaje de tienda
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    mostrar_nuevo_piso(call.message.chat.id, user_id)

# ---------- ACCIONES DE BATALLA ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("accion_"))
def accion_batalla(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if user_id not in partidas:
        return

    partida = partidas[user_id]
    
    # Anti-spam
    if partida.get("procesando"):
        return
    
    partida["procesando"] = True
    partida["ultimo_acceso"] = time.time()

    try:
        monstruo = partida.get("monstruo_actual")
        if monstruo is None:
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
            if random.random() < 0.6:
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
            # Sumar oro de la partida actual al progreso
            progreso[user_id]["oro"] = progreso[user_id].get("oro", 0) + partida.get("oro_ganado", 0)
            progreso[user_id]["experiencia"] += exp_ganada
            progreso[user_id]["piso_maximo"] = max(progreso[user_id].get("piso_maximo", 0), partida["piso"])
            guardar_progreso()

            try:
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
            except:
                pass
            partidas.pop(user_id, None)
            return

        if monstruo["vida"] <= 0:
            oro_ganado = monstruo["oro"]
            xp_ganada = monstruo["xp"]
            partida["oro_ganado"] = partida.get("oro_ganado", 0) + oro_ganado
            progreso[user_id]["oro"] = progreso[user_id].get("oro", 0) + oro_ganado
            progreso[user_id]["experiencia"] += xp_ganada
            partida["piso"] += 1
            partida["vida"] = min(partida["vida"] + 10, 100)
            progreso[user_id]["piso_actual"] = partida["piso"]
            partida["monstruo_actual"] = None
            partida["acciones_sin_guardar"] += 1
            if partida["acciones_sin_guardar"] >= 10:
                guardar_progreso()
                partida["acciones_sin_guardar"] = 0

            try:
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
            except:
                pass

            # Timer con verificación de partida activa
            def timer_callback():
                if user_id in partidas and partidas[user_id].get("piso") == partida["piso"]:
                    mostrar_nuevo_piso(chat_id, user_id)

            threading.Timer(5, timer_callback).start()
            return

        nuevo_texto = (
            f"{resultado}\n\n"
            f"{monstruo['emoji']} 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['nombre']}\n"
            f"❤️ 𝗩𝗜𝗗𝗔 𝗠𝗢𝗡𝗦𝗧𝗥𝗨𝗢: {monstruo['vida']}\n\n"
            f"❤️ 𝗧𝗨 𝗩𝗜𝗗𝗔: {partida['vida']}\n"
            f"⚔️ 𝗣𝗢𝗗𝗘𝗥 𝗗𝗘 𝗔𝗧𝗔𝗤𝗨𝗘: {partida['arma_daño']}\n"
            f"💊 𝗧𝗨𝗦 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦: {partida['pociones']}\n"
            f"🪙 𝗧𝗨 𝗢𝗥𝗢: {progreso[user_id].get('oro', 0)}\n\n"
            "¿𝗤𝘂𝗲́ 𝗱𝗲𝘀𝗲𝗮𝘀 𝗵𝗮𝗰𝗲𝗿?"
        )

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("⚔️ 𝗔𝗧𝗔𝗖𝗔𝗥", callback_data="accion_atacar"),
            InlineKeyboardButton("🛡️ 𝗗𝗘𝗙𝗘𝗡𝗗𝗘𝗥", callback_data="accion_defender"),
            InlineKeyboardButton("✨ 𝗠𝗔𝗚𝗜𝗔 - 𝘔𝘢𝘨𝘪𝘤 𝘢𝘵𝘵𝘢𝘤𝘬 %60", callback_data="accion_magia"),
            InlineKeyboardButton("💊 𝗣𝗢𝗖𝗜𝗢𝗡 - 𝘊𝘢𝘳𝘨𝘢𝘳 𝘷𝘪𝘥𝘢 +50", callback_data="accion_pocion"),
            InlineKeyboardButton("🛒 𝗧𝗜𝗘𝗡𝗗𝗔", callback_data="abrir_tienda")
        )

        try:
            if partida.get("message_id"):
                bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=partida["message_id"],
                    caption=nuevo_texto,
                    reply_markup=markup
                )
            else:
                msg = bot.send_message(chat_id, nuevo_texto, reply_markup=markup)
                partida["message_id"] = msg.message_id
        except:
            try:
                msg = bot.send_message(chat_id, nuevo_texto, reply_markup=markup)
                partida["message_id"] = msg.message_id
            except:
                pass
    finally:
        partida["procesando"] = False

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
        f"⭐ 𝗘𝗫𝗣𝗘𝗥𝗜𝗘𝗡𝗖𝗜𝗔: {p.get('experiencia', 0)}\n"
        f"💊 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦: {p.get('pociones', 0)}"
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
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Error en polling: {e}")
            time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
