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
IMAGEN_CAIDO = f"{BASE_URL}/jugador_caido.jpg"

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
            "nivel": 1,
            "piso_actual": 1,
            "arma_daño": 10,
            "pociones": 1,
            "mejor_racha": 0,
        }
        guardar_progreso()

    partidas[user_id] = {
        "vida": 200,
        "vida_maxima": 200,
        "piso": 1,
        "arma_daño": progreso[user_id].get("arma_daño", 10),
        "pociones": min(progreso[user_id].get("pociones", 1), 3),
        "monstruo_actual": None,
        "message_id": None,
        "oro_ganado": 0,
        "ultimo_acceso": time.time(),
        "procesando": False,
        "acciones_sin_guardar": 0,
        "racha": 0,
        "turnos_sin_pocion": 3,
        "turnos_sin_magia": 3,
        "compras_en_piso": 0,
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
        "Daño normal al monstruo.\n"
        "15% de golpe crítico (doble daño).\n\n"
        "💥 𝗖𝗥𝗜𝗧𝗜𝗖𝗔𝗟 𝗔𝗧𝗧𝗔𝗖𝗞\n"
        "Daño aumentado (x1.5).\n"
        "Recibes daño normal.\n\n"
        "✨ 𝗠𝗔𝗚𝗜𝗔\n"
        "Daño masivo, pero puede fallar.\n"
        "60% de probabilidad de éxito.\n"
        "Solo 1 vez cada 3 turnos.\n\n"
        "💊 𝗣𝗢𝗖𝗜𝗢𝗡\n"
        "Recupera 25 puntos de vida.\n"
        "Máximo 3 pociones.\n"
        "Solo 1 vez cada 3 turnos.\n"
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

    # Resetear compras en piso
    partida["compras_en_piso"] = 0

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
        InlineKeyboardButton("💥 𝗖𝗥𝗜𝗧𝗜𝗖𝗔𝗟 𝗔𝗧𝗧𝗔𝗖𝗞", callback_data="accion_defender"),
        InlineKeyboardButton("✨ 𝗠𝗔𝗚𝗜𝗔 - 𝘔𝘢𝘨𝘪𝘤 𝘢𝘵𝘵𝘢𝘤𝘬 %60", callback_data="accion_magia"),
        InlineKeyboardButton("💊 𝗣𝗢𝗖𝗜𝗢𝗡 - 𝘊𝘢𝘳𝘨𝘢𝘳 𝘷𝘪𝘥𝘢 +25", callback_data="accion_pocion"),
        InlineKeyboardButton("🛒 𝗧𝗜𝗘𝗡𝗗𝗔", callback_data="abrir_tienda")
    )

    texto = (
        f"🗼 <b>Piso {piso}</b> - {monstruo['zona']}\n"
        f"{monstruo['mundo']}\n\n"
        f"{monstruo['descripcion']}\n\n"
        f"{monstruo['emoji']} <b>Monstruo:</b> {monstruo['nombre']}\n"
        f"❤️ <b>Vida del monstruo:</b> {monstruo['vida']}\n"
        f"⚔️ <b>Daño del monstruo:</b> {monstruo['daño']}\n"
        f"─────────────────\n"
        f"❤️ <b>Tu vida:</b> {partida['vida']}/{partida['vida_maxima']}\n"
        f"⚔️ <b>Poder de ataque:</b> {partida['arma_daño']}\n"
        f"💊 <b>Tus pociones:</b> {partida['pociones']}/3\n"
        f"🪙 <b>Tu oro:</b> {progreso[user_id].get('oro', 0)}\n"
        f"🔥 <b>Racha:</b> {partida['racha']}\n\n"
        f"<b>¿Qué deseas hacer?</b>"
    )

    # Usar caché de imágenes con validación
    if imagen_url not in imagenes_cache:
        try:
            r = requests.get(imagen_url, timeout=10)
            if r.status_code == 200:
                if len(imagenes_cache) >= MAX_CACHE_SIZE:
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
                reply_markup=markup,
                parse_mode='HTML'
            )
        else:
            msg = bot.send_message(chat_id, texto, reply_markup=markup, parse_mode='HTML')
        partida["message_id"] = msg.message_id
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        try:
            msg = bot.send_message(chat_id, texto, reply_markup=markup, parse_mode='HTML')
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

    # Precio escalonado
    pociones_actuales = partidas[user_id]["pociones"]
    if pociones_actuales >= 3:
        precio = 999
    elif pociones_actuales == 2:
        precio = 80
    elif pociones_actuales == 1:
        precio = 40
    else:
        precio = 20

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"💊 Comprar Poción - {precio} oro", callback_data="comprar_pocion"),
        InlineKeyboardButton("⬅️ Volver", callback_data="volver_batalla")
    )

    try:
        if pociones_actuales >= 3:
            bot.send_message(call.message.chat.id,
                "🛒 𝗧𝗜𝗘𝗡𝗗𝗔 𝗗𝗘 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦\n\n"
                f"🪙 Tu oro: {progreso[user_id].get('oro', 0)}\n\n"
                "❌ 𝗧𝗜𝗘𝗡𝗘𝗦 𝗘𝗟 𝗠𝗔𝗫𝗜𝗠𝗢 𝗗𝗘 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦 (3)\n\n"
                "Usa una poción antes de comprar otra.",
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id,
                "🛒 𝗧𝗜𝗘𝗡𝗗𝗔 𝗗𝗘 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦\n\n"
                f"🪙 Tu oro: {progreso[user_id].get('oro', 0)}\n"
                "💊 Poción de vida +25\n"
                f"💰 Costo: {precio} de oro\n\n"
                "⚠️ Precio aumenta con cada poción.\n"
                "Máximo 3 pociones por partida.",
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

    partida = partidas[user_id]
    partida["ultimo_acceso"] = time.time()

    # Verificar que no haya comprado ya en este piso
    if partida["compras_en_piso"] >= 1:
        try:
            bot.send_message(call.message.chat.id,
                "❌ 𝗖𝗢𝗠𝗣𝗥𝗔 𝗕𝗟𝗢𝗤𝗨𝗘𝗔𝗗𝗔\n\n"
                "Solo puedes comprar 1 poción por piso.\n"
                "Sube de piso para comprar otra."
            )
        except:
            pass
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        mostrar_nuevo_piso(call.message.chat.id, user_id)
        return

    pociones_actuales = partida["pociones"]
    if pociones_actuales >= 3:
        try:
            bot.send_message(call.message.chat.id,
                "❌ 𝗧𝗜𝗘𝗡𝗘𝗦 𝗘𝗟 𝗠𝗔𝗫𝗜𝗠𝗢 𝗗𝗘 𝗣𝗢𝗖𝗜𝗢𝗡𝗘𝗦 (3)\n\n"
                "Usa una poción antes de comprar otra."
            )
        except:
            pass
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        mostrar_nuevo_piso(call.message.chat.id, user_id)
        return

    # Precio escalonado
    if pociones_actuales == 2:
        precio = 80
    elif pociones_actuales == 1:
        precio = 40
    else:
        precio = 20

    oro = progreso[user_id].get("oro", 0)

    if oro >= precio:
        progreso[user_id]["oro"] = oro - precio
        partida["pociones"] += 1
        partida["compras_en_piso"] = 1
        partida["acciones_sin_guardar"] += 1
        if partida["acciones_sin_guardar"] >= 10:
            guardar_progreso()
            partida["acciones_sin_guardar"] = 0
        try:
            bot.send_message(call.message.chat.id,
                "✅ 𝗖𝗢𝗠𝗣𝗥𝗔 𝗘𝗫𝗜𝗧𝗢𝗦𝗔\n\n"
                f"💊 Poción comprada por {precio} de oro.\n"
                f"Tienes {partida['pociones']}/3 pociones.\n"
                f"🪙 Oro restante: {progreso[user_id]['oro']}"
            )
        except:
            pass
    else:
        try:
            bot.send_message(call.message.chat.id,
                f"❌ 𝗢𝗥𝗢 𝗜𝗡𝗦𝗨𝗙𝗜𝗖𝗜𝗘𝗡𝗧𝗘\n\n"
                f"Necesitas {precio} de oro para comprar.\n"
                f"Tienes {oro} de oro."
            )
        except:
            pass

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
        critico = False

        # Incrementar turnos
        partida["turnos_sin_pocion"] += 1
        partida["turnos_sin_magia"] += 1

        if accion == "accion_atacar":
            daño = partida["arma_daño"]
            # 15% de crítico
            if random.random() < 0.15:
                daño = daño * 2
                critico = True
            monstruo["vida"] -= daño
            daño_recibido = monstruo["daño"]
            partida["vida"] -= daño_recibido
            if critico:
                resultado = f"⚡ <b>GOLPE CRÍTICO</b> - Daño doble ({daño})"
            else:
                resultado = f"⚔️ <b>ATAQUE</b> - Daño ({daño})"

        elif accion == "accion_defender":
            daño = int(partida["arma_daño"] * 1.5)
            monstruo["vida"] -= daño
            daño_recibido = monstruo["daño"]
            partida["vida"] -= daño_recibido
            resultado = f"💥 <b>CRITICAL ATTACK</b> - Daño aumentado ({daño})"

        elif accion == "accion_magia":
            if partida["turnos_sin_magia"] < 3:
                resultado = "⏳ <b>MAGIA EN ENFRIAMIENTO</b>\n\nDebes esperar 3 turnos entre magias."
            else:
                if random.random() < 0.6:
                    daño = partida["arma_daño"] * 3
                    monstruo["vida"] -= daño
                    daño_recibido = monstruo["daño"]
                    partida["vida"] -= daño_recibido
                    resultado = f"✨ <b>MAGIA EXITOSA</b> - Daño masivo ({daño})"
                    partida["turnos_sin_magia"] = 0
                else:
                    daño_recibido = monstruo["daño"] * 2
                    partida["vida"] -= daño_recibido
                    resultado = f"❌ <b>MAGIA FALLÓ</b> - Daño doble recibido ({daño_recibido})"
                    partida["turnos_sin_magia"] = 0

        elif accion == "accion_pocion":
            if partida["turnos_sin_pocion"] < 3:
                resultado = "⏳ <b>POCIÓN EN ENFRIAMIENTO</b>\n\nDebes esperar 3 turnos entre pociones."
            else:
                if partida["pociones"] > 0:
                    partida["pociones"] -= 1
                    partida["vida"] += 25
                    if partida["vida"] > partida["vida_maxima"]:
                        partida["vida"] = partida["vida_maxima"]
                    resultado = f"💊 <b>POCIÓN USADA</b> - +25 vida ({partida['vida']}/{partida['vida_maxima']})"
                    partida["turnos_sin_pocion"] = 0
                else:
                    resultado = "❌ <b>NO TIENES POCIONES</b>"

        if partida["vida"] <= 0:
            exp_ganada = partida["piso"] * 2
            # Sumar oro de la partida actual al progreso
            progreso[user_id]["oro"] = progreso[user_id].get("oro", 0) + partida.get("oro_ganado", 0)
            progreso[user_id]["experiencia"] += exp_ganada
            progreso[user_id]["piso_maximo"] = max(progreso[user_id].get("piso_maximo", 0), partida["piso"])
            
            # Guardar mejor racha
            if partida["racha"] > progreso[user_id].get("mejor_racha", 0):
                progreso[user_id]["mejor_racha"] = partida["racha"]
            
            guardar_progreso()

            texto_muerte = (
                f"💀 <b>HAS CAÍDO EN BATALLA</b>\n\n"
                f"{monstruo['emoji']} <b>{monstruo['nombre']}</b> te ha derrotado en el piso {partida['piso']}.\n\n"
                f"⭐ <b>Experiencia ganada:</b> {exp_ganada}\n"
                f"🪙 <b>Oro acumulado:</b> {progreso[user_id].get('oro', 0)}\n"
                f"🗼 <b>Piso máximo alcanzado:</b> {progreso[user_id]['piso_maximo']}\n"
                f"🔥 <b>Racha de victorias:</b> {partida['racha']}\n\n"
                f"La torre te espera de nuevo.\n"
                f"Escribe /torre para volver a intentarlo.\n\n"
                f"<i>“No es el fin, solo una pausa en tu leyenda.”</i>"
            )

            try:
                r = requests.get(IMAGEN_CAIDO, timeout=10)
                if r.status_code == 200:
                    bot.send_photo(
                        chat_id,
                        photo=r.content,
                        caption=texto_muerte,
                        parse_mode='HTML'
                    )
                else:
                    bot.send_message(chat_id, texto_muerte, parse_mode='HTML')
            except:
                try:
                    bot.send_message(chat_id, texto_muerte, parse_mode='HTML')
                except:
                    pass
            partidas.pop(user_id, None)
            return

        if monstruo["vida"] <= 0:
            oro_ganado = monstruo["oro"]
            xp_ganada = monstruo["xp"]
            
            # Bonus por racha en rangos
            bonus_racha = 0
            if partida["racha"] >= 10:
                bonus_racha = 50
            elif partida["racha"] >= 5:
                bonus_racha = 25
            elif partida["racha"] >= 3:
                bonus_racha = 10
            
            oro_ganado += bonus_racha
            
            partida["oro_ganado"] = partida.get("oro_ganado", 0) + oro_ganado
            progreso[user_id]["oro"] = progreso[user_id].get("oro", 0) + oro_ganado
            progreso[user_id]["experiencia"] += xp_ganada
            partida["piso"] += 1
            partida["racha"] += 1
            
            # Vida recuperada escalada con el piso
            vida_recuperada = min(5 + (partida["piso"] // 5) * 3, 10)
            partida["vida"] = min(partida["vida"] + vida_recuperada, partida["vida_maxima"])
            
            progreso[user_id]["piso_actual"] = partida["piso"]
            partida["monstruo_actual"] = None
            partida["acciones_sin_guardar"] += 1
            if partida["acciones_sin_guardar"] >= 10:
                guardar_progreso()
                partida["acciones_sin_guardar"] = 0

            if bonus_racha > 0:
                texto_racha = f"\n🔥 <b>BONUS POR RACHA:</b> +{bonus_racha} de oro"
            else:
                texto_racha = ""

            try:
                bot.send_message(chat_id,
                    f"⚔️ <b>VICTORIA</b>\n\n"
                    f"Has derrotado a:\n"
                    f"{monstruo['emoji']} <b>{monstruo['nombre']}</b>\n\n"
                    f"🪙 <b>Oro ganado:</b> {oro_ganado}{texto_racha}\n"
                    f"⭐ <b>Experiencia:</b> {xp_ganada}\n"
                    f"❤️ <b>Vida recuperada:</b> +{vida_recuperada}\n"
                    f"🔥 <b>Racha actual:</b> {partida['racha']}\n\n"
                    f"🗼 <b>Piso alcanzado:</b> {partida['piso']}\n\n"
                    f"⏳ El siguiente monstruo aparecerá en 5 segundos...",
                    parse_mode='HTML'
                )
            except:
                pass

            def timer_callback():
                if user_id in partidas and partidas[user_id].get("piso") == partida["piso"]:
                    mostrar_nuevo_piso(chat_id, user_id)

            threading.Timer(5, timer_callback).start()
            return

        nuevo_texto = (
            f"{resultado}\n\n"
            f"{monstruo['emoji']} <b>Monstruo:</b> {monstruo['nombre']}\n"
            f"❤️ <b>Vida del monstruo:</b> {monstruo['vida']}\n"
            f"⚔️ <b>Daño del monstruo:</b> {monstruo['daño']}\n"
            f"─────────────────\n"
            f"❤️ <b>Tu vida:</b> {partida['vida']}/{partida['vida_maxima']}\n"
            f"⚔️ <b>Poder de ataque:</b> {partida['arma_daño']}\n"
            f"💊 <b>Tus pociones:</b> {partida['pociones']}/3\n"
            f"🪙 <b>Tu oro:</b> {progreso[user_id].get('oro', 0)}\n"
            f"🔥 <b>Racha:</b> {partida['racha']}\n\n"
            f"<b>¿Qué deseas hacer?</b>"
        )

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("⚔️ 𝗔𝗧𝗔𝗖𝗔𝗥", callback_data="accion_atacar"),
            InlineKeyboardButton("💥 𝗖𝗥𝗜𝗧𝗜𝗖𝗔𝗟 𝗔𝗧𝗧𝗔𝗖𝗞", callback_data="accion_defender"),
            InlineKeyboardButton("✨ 𝗠𝗔𝗚𝗜𝗔 - 𝘔𝘢𝘨𝘪𝘤 𝘢𝘵𝘵𝘢𝘤𝘬 %60", callback_data="accion_magia"),
            InlineKeyboardButton("💊 𝗣𝗢𝗖𝗜𝗢𝗡 - 𝘊𝘢𝘳𝘨𝘢𝘳 𝘷𝘪𝘥𝘢 +25", callback_data="accion_pocion"),
            InlineKeyboardButton("🛒 𝗧𝗜𝗘𝗡𝗗𝗔", callback_data="abrir_tienda")
        )

        try:
            if partida.get("message_id"):
                bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=partida["message_id"],
                    caption=nuevo_texto,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                msg = bot.send_message(chat_id, nuevo_texto, reply_markup=markup, parse_mode='HTML')
                partida["message_id"] = msg.message_id
        except:
            try:
                msg = bot.send_message(chat_id, nuevo_texto, reply_markup=markup, parse_mode='HTML')
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
        f"📊 <b>𝗧𝗨 𝗣𝗥𝗢𝗚𝗥𝗘𝗦𝗢</b>\n\n"
        f"👤 <b>Nombre:</b> {p['nombre']}\n"
        f"🗼 <b>Piso máximo:</b> {p.get('piso_maximo', 0)}\n"
        f"🪙 <b>Oro:</b> {p.get('oro', 0)}\n"
        f"⭐ <b>Experiencia:</b> {p.get('experiencia', 0)}\n"
        f"🔥 <b>Mejor racha:</b> {p.get('mejor_racha', 0)}\n"
        f"💊 <b>Pociones:</b> {p.get('pociones', 0)}",
        parse_mode='HTML'
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

    texto = "🏆 <b>𝗥𝗔𝗡𝗞𝗜𝗡𝗚 𝗗𝗘 𝗟𝗔 𝗧𝗢𝗥𝗥𝗘</b>\n\n"
    for i, (user_id, datos) in enumerate(ranking[:10], 1):
        texto += f"{i}. {datos['nombre']} - Piso {datos.get('piso_maximo', 0)}\n"

    bot.reply_to(message, texto, parse_mode='HTML')

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
