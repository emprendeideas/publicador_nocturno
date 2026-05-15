import os
import random
import uuid
import requests
import asyncio

from zoneinfo import ZoneInfo
from datetime import datetime
import locale

from telethon import TelegramClient
from pymongo import MongoClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from threading import Thread

# =========================================================
# CONFIG
# =========================================================

API_ID = int(os.getenv("API_ID"))

API_HASH = os.getenv("API_HASH")

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = -1003933999548

FDI_CHANNEL_ID = -1003934627486

MONGO_URI = os.getenv("MONGO_URI")

# =========================================
# 🔹 FLASK PARA RENDER
# =========================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de Stories activo 🚀"

def run_web():

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )

def iniciar_web():

    t = Thread(
        target=run_web
    )

    t.start()

# =========================================================
# TELEGRAM
# =========================================================

client = TelegramClient(
    "/tmp/bot_publicador_noche",
    API_ID,
    API_HASH,
    connection_retries=None,
    retry_delay=5,
    auto_reconnect=True
)

# =========================================================
# MONGODB
# =========================================================

mongo_client = MongoClient(MONGO_URI)

db = mongo_client["telegram_states"]

stories_col = db["stories"]

publicadas_col = db["canal_publicadas"]

# =========================================================
# TEXTOS
# =========================================================

PAGOS_TEXTOS = [
    """🎉 Cada semana más personas están entrando a nuestras [Herramientas](https://beacons.ai/nanomillenial) premium 🚀

Estos son algunos pagos de Hoy, (HOY) y accesos entregados recientemente ✅

📌 Acceso inmediato
💰 UN SOLO PAGO
📈 Herramientas Automatizadas Reales

Si quieres información escríbeme ahora para tener Precios de Pomoción 👇

⭐ [Nano Bots](https://t.me/NanoMillenial)
""",

    """🚀 Más usuarios siguen activando nuestras [Herramientas](https://beacons.ai/nanomillenial) premium cada semana ✅

Este (HOY) les mostramos compras y accesos reales de los usuarios ingresando todos los días 📈

💰 Herramientas exclusivas
⚡ Acceso inmediato
🤖 Sistemas automatizados

Si quieres información escríbeme ahora 👇

⭐ [Nano Bots](https://t.me/NanoMillenial)
"""
]

FDI_TEXTOS = [
    """💬 Seguimos recibiendo mensajes de usuarios satisfechos 🚀

Muchas personas siguen ingresando Hoy, (HOY), al [Fondo de Inversión FDI](https://t.me/inversionesFDI) y nos comparten sus resultados ✅

📊 Solo 5 días de operación
🤖 Puede ingresa las veces que desee
🔥 Ganancia del 50% FIJO

Si quiere conocer cómo funciona todo, escríbame 👇

⭐ [Nano Bots](https://t.me/NanoMillenial)
""",

    """🔥 Cada vez más personas ingresan al [Fondo de Inversión FDI](https://t.me/inversionesFDI) con Ganancias Automatizadas 🚀

Este (HOY) tenemos algunos mensajes y experiencias reales de usuarios ✅

📈 Resultado Fijo del 50%
⚡ Interes compuesto inteligente
🤖 Operativa de solo 5 días

🚀 Mira todos los [Testimonios y pagos](https://t.me/inversionesFDI)
Escríbame ahora para información detallada 👇

⭐ [Nano Bots](https://t.me/NanoMillenial)
"""
]

COPYTRADE_TEXTOS = [
    """📈 Nuevos resultados del sistema CopyTrade automático 🚀

Estas son algunas Operaciones Reales ejecutadas Hoy, (HOY), en mercado en tiempo real ✅

🤖 Sistema automatizado
📊 Resultados constantes
⚡ Sin necesidad de experiencia

Una Gran Oportunidad...

Click y escríbeme 👇

⭐ [NanoBots](https://t.me/NanoMillenial)
""",

    """🚀 El sistema CopyTrade sigue generando ingresos en tiempo real

Resultados automáticos este (HOY) y operaciones ejecutadas por el sistema ✅

🤖 Automatización completa
📊 Trading inteligente
⚡ Operaciones todos los días

Todavia tenemos espacios en el sistema...

Click y escríbeme 👇

⭐ [NanoBots](https://t.me/NanoMillenial)
"""
]

# =========================================================
# FECHA ACTUAL EN ESPAÑOL
# =========================================================

def obtener_fecha_hoy():

    dias = {
        "Monday": "lunes",
        "Tuesday": "martes",
        "Wednesday": "miércoles",
        "Thursday": "jueves",
        "Friday": "viernes",
        "Saturday": "sábado",
        "Sunday": "domingo"
    }

    meses = {
        1: "enero",
        2: "febrero",
        3: "marzo",
        4: "abril",
        5: "mayo",
        6: "junio",
        7: "julio",
        8: "agosto",
        9: "septiembre",
        10: "octubre",
        11: "noviembre",
        12: "diciembre"
    }

    ahora = datetime.now()

    dia_semana = dias[ahora.strftime("%A")]

    dia = ahora.day

    mes = meses[ahora.month]

    return f"{dia_semana} {dia} de {mes}"

# =========================================================
# UTILIDADES
# =========================================================

def obtener_texto(tipo):

    hoy = obtener_fecha_hoy()

    if tipo == "pagos":
        texto = random.choice(PAGOS_TEXTOS)

    elif tipo == "fdi":
        texto = random.choice(FDI_TEXTOS)

    elif tipo == "copytrade":
        texto = random.choice(COPYTRADE_TEXTOS)

    else:
        texto = "🚀"

    return texto.replace("(HOY)", hoy)

# =========================================================

def descargar_imagen(url):

    nombre = f"temp_{uuid.uuid4()}.jpg"

    response = requests.get(url, timeout=20)

    with open(nombre, "wb") as f:
        f.write(response.content)

    return nombre

# =========================================================

def obtener_stories(tipo, cantidad):

    publicados = list(
        publicadas_col.find(
            {"tipo": tipo},
            {"story_id": 1}
        )
    )

    ids_publicados = [
        p["story_id"] for p in publicados
    ]

    disponibles = list(
        stories_col.find({
            "tipo": tipo,
            "_id": {
                "$nin": ids_publicados
            }
        })
    )

    # =====================================================
    # RESET AUTOMÁTICO
    # =====================================================

    if len(disponibles) < cantidad:

        print(f"♻️ Reiniciando historial de {tipo}")

        publicadas_col.delete_many({
            "tipo": tipo
        })

        disponibles = list(
            stories_col.find({
                "tipo": tipo
            })
        )

    # =====================================================

    if cantidad == 1:
        seleccionadas = [random.choice(disponibles)]
    else:
        seleccionadas = random.sample(
            disponibles,
            cantidad
        )

    return seleccionadas

# =========================================================

async def publicar(tipo, cantidad):

    try:

        print(f"🚀 Publicando {tipo}")

        stories = obtener_stories(
            tipo,
            cantidad
        )

        archivos = []

        for story in stories:

            archivo = descargar_imagen(
                story["imagen"]
            )

            archivos.append(archivo)

        texto = obtener_texto(tipo)

        # =================================================
        # PUBLICAR CANAL PRINCIPAL
        # =================================================

        await client.send_file(
            entity=CHANNEL_ID,
            file=archivos,
            caption=texto,
            parse_mode="md"
        )

        # =================================================
        # PUBLICAR TAMBIÉN EN CANAL FDI
        # =================================================

        if tipo == "fdi":

            await client.send_file(
                entity=FDI_CHANNEL_ID,
                file=archivos,
                caption=texto,
                parse_mode="md"
            )

        # =================================================
        # GUARDAR HISTORIAL
        # =================================================

        for story in stories:

            publicadas_col.insert_one({
                "story_id": story["_id"],
                "tipo": tipo,
                "fecha": datetime.now()
            })

        print(f"✅ Publicación completada: {tipo}")

        # =================================================
        # ELIMINAR TEMPORALES
        # =================================================

        for archivo in archivos:

            try:
                os.remove(archivo)
            except:
                pass

    except Exception as e:

        print(f"❌ Error publicando {tipo}: {e}")

# =========================================================
# WRAPPERS SCHEDULER
# =========================================================

async def ejecutar_pagos():

    await publicar("pagos", 1)

async def ejecutar_copytrade():

    await publicar("copytrade", 2)

async def ejecutar_fdi():

    await publicar("fdi", 2)

# =========================================================
# SCHEDULER
# =========================================================

scheduler = AsyncIOScheduler(
    timezone=ZoneInfo("America/La_Paz")
)

# =========================================================
# PAGOS
# Lunes a Sábado
# 19:30
# =========================================================

scheduler.add_job(
    ejecutar_pagos,
    CronTrigger(
        day_of_week="mon,tue,wed,thu,fri,sat",
        hour=19,
        minute=30
        timezone="America/La_Paz"
    )
)

# =========================================================
# COPYTRADE
# Lunes a Sábado
# 21:00
# =========================================================

scheduler.add_job(
    ejecutar_copytrade,
    CronTrigger(
        day_of_week="mon,tue,wed,thu,fri,sat",
        hour=21,
        minute=0
        timezone="America/La_Paz"
    )
)

# =========================================================
# FDI
# Lunes a Sábado
# 22:30
# =========================================================

scheduler.add_job(
    ejecutar_fdi,
    CronTrigger(
        day_of_week="mon,tue,wed,thu,fri,sat",
        hour=22,
        minute=30
        timezone="America/La_Paz"
    )
)

# =========================================================
# MAIN TELEGRAM
# =========================================================

async def main():

    print("🚀 PUBLICADOR NOCTURNO ACTIVO EN RENDER")
    print("🔌 Iniciando Telegram...")

    iniciar_web()

    await client.connect()

    if not await client.is_user_authorized():

        await client.start(
            bot_token=BOT_TOKEN
        )

    print("✅ Telegram conectado:", client.is_connected())
    print("✅ Sesión Telegram iniciada correctamente")

    scheduler.start()

    print("✅ Scheduler iniciado")

    await client.run_until_disconnected()

# =========================================================
# EJECUTAR
# =========================================================

if __name__ == "__main__":

    asyncio.run(main())