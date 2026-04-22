from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ──────────────────────────────────────────────
# CONFIGURACIÓN - Reemplaza estos valores
# ──────────────────────────────────────────────
VERIFY_TOKEN = "movistar2026"       # Pon cualquier palabra clave tuya
WHATSAPP_TOKEN = "EAAN08XeNqq4BRS8hS3UeEktHz2PTGXkrmZCZA7WMPpaBYrUjQCD115AnMfuIMOB5OyRcRDMCaadmoph0yLpnUzeDdK2MEyzbWw1khUGu6PtEJQlLDDCV26AMIhRmmWS2I85BljU9jmbBqxyhLwAMnZAZCEQ1JRZCtpiDygBNNwKFBO17CdqPZBvR4t2yC2ZBG8ONddaQq5LLKL1PpoXXYcG5PyEtHdFFhf7YVfZCCx6284WCLTUkZAnRUTQpg1fbSpyRVXl1QBkWeugMmTGSdTpmYiAZDZD"   # Token de Meta Business API
PHONE_NUMBER_ID = "1083765808157143"      # ID de tu número en Meta
TU_NUMERO = "51906783403"                   # Tu número para recibir leads (con código de país)

# ──────────────────────────────────────────────
# PLANES MOVISTAR
# ──────────────────────────────────────────────
PLANES = {
    "1": {
        "nombre": "Plan Solo Internet",
        "precio": "S/ 50",
        "incluye": "Internet de alta velocidad + Disney+ Gratis",
        "detalle": "Ideal si solo necesitas navegar, trabajar o estudiar desde casa."
    },
    "2": {
        "nombre": "Plan Dúo (Internet + Cable)",
        "precio": "S/ 85",
        "incluye": "Internet + Cable TV + Disney+ Gratis + Max Gratis",
        "detalle": "Perfecta combinación para entretenimiento y navegación."
    },
    "3": {
        "nombre": "Plan Trío (Internet + Cable + Teléfono Fijo)",
        "precio": "S/ 90",
        "incluye": "Internet + Cable TV + Teléfono Fijo + Disney+ Gratis + Max Gratis",
        "detalle": "El plan más completo para toda la familia."
    }
}

# ──────────────────────────────────────────────
# MEMORIA DE CONVERSACIÓN (simple, en RAM)
# ──────────────────────────────────────────────
conversaciones = {}

# ──────────────────────────────────────────────
# LÓGICA DEL BOT
# ──────────────────────────────────────────────
def obtener_respuesta(numero, mensaje):
    msg = mensaje.strip().lower()

    # Iniciar conversación o reiniciar
    if msg in ["hola", "buenas", "buenos días", "buenas tardes", "buenas noches", "inicio", "menu", "menú"]:
        conversaciones[numero] = {"estado": "menu"}
        return (
            "¡Hola! 👋 Bienvenido a *Movistar Internet Hogar*.\n\n"
            "Soy tu asesor virtual y estoy aquí para ayudarte a encontrar el plan perfecto para ti. 😊\n\n"
            "¿Qué deseas hacer?\n\n"
            "1️⃣ Ver planes y precios\n"
            "2️⃣ Hablar con un asesor\n"
            "3️⃣ Ya soy cliente Movistar\n\n"
            "Responde con el número de tu opción."
        )

    estado = conversaciones.get(numero, {}).get("estado", "inicio")

    # ── MENÚ PRINCIPAL ──
    if estado == "menu":
        if msg == "1":
            conversaciones[numero]["estado"] = "ver_planes"
            return (
                "📦 *Nuestros Planes Movistar Internet Hogar:*\n\n"
                "1️⃣ *Solo Internet* → S/ 50/mes\n"
                "   ✅ Disney+ Gratis\n\n"
                "2️⃣ *Dúo (Internet + Cable)* → S/ 85/mes\n"
                "   ✅ Disney+ Gratis\n"
                "   ✅ Max Gratis\n\n"
                "3️⃣ *Trío (Internet + Cable + Teléfono)* → S/ 90/mes\n"
                "   ✅ Disney+ Gratis\n"
                "   ✅ Max Gratis\n\n"
                "Escribe el número del plan para ver más detalles. 👇"
            )
        elif msg == "2":
            conversaciones[numero]["estado"] = "lead"
            notificar_lead(numero, "Quiere hablar con asesor")
            return (
                "📞 Perfecto, un asesor se comunicará contigo muy pronto.\n\n"
                "Mientras tanto, ¿puedes contarme tu nombre y en qué distrito estás? "
                "Así agilizamos tu atención. 😊"
            )
        elif msg == "3":
            conversaciones[numero]["estado"] = "cliente_existente"
            return (
                "¡Gracias por ser cliente Movistar! 💙\n\n"
                "¿En qué podemos ayudarte?\n\n"
                "1️⃣ Consultar mi plan actual\n"
                "2️⃣ Mejorar mi plan\n"
                "3️⃣ Reportar un problema\n\n"
                "Responde con el número."
            )
        else:
            return "Por favor responde con *1*, *2* o *3*. 😊"

    # ── VER DETALLE DE UN PLAN ──
    elif estado == "ver_planes":
        if msg in ["1", "2", "3"]:
            plan = PLANES[msg]
            conversaciones[numero]["estado"] = f"plan_{msg}"
            conversaciones[numero]["plan_seleccionado"] = plan["nombre"]
            return (
                f"📋 *{plan['nombre']}*\n"
                f"💰 Precio: {plan['precio']}/mes\n"
                f"🎁 Incluye: {plan['incluye']}\n\n"
                f"💬 {plan['detalle']}\n\n"
                "¿Te interesa este plan?\n\n"
                "1️⃣ Sí, quiero contratar\n"
                "2️⃣ Ver otros planes\n"
                "3️⃣ Volver al menú principal"
            )
        else:
            return "Por favor elige un plan escribiendo *1*, *2* o *3*. 😊"

    # ── DECISIÓN TRAS VER UN PLAN ──
    elif estado.startswith("plan_"):
        if msg == "1":
            plan_nombre = conversaciones[numero].get("plan_seleccionado", "un plan")
            conversaciones[numero]["estado"] = "recopilando_datos"
            notificar_lead(numero, f"Interesado en: {plan_nombre}")
            return (
                f"¡Excelente elección! 🎉\n\n"
                f"Para procesar tu solicitud de *{plan_nombre}*, necesito algunos datos:\n\n"
                "📝 ¿Cuál es tu *nombre completo*?"
            )
        elif msg == "2":
            conversaciones[numero]["estado"] = "ver_planes"
            return (
                "Claro, aquí están todos los planes:\n\n"
                "1️⃣ Solo Internet → S/ 50/mes\n"
                "2️⃣ Dúo (Internet + Cable) → S/ 85/mes\n"
                "3️⃣ Trío (Internet + Cable + Tel.) → S/ 90/mes\n\n"
                "Escribe el número del plan para ver detalles."
            )
        elif msg == "3":
            conversaciones[numero]["estado"] = "menu"
            return (
                "Menú principal:\n\n"
                "1️⃣ Ver planes y precios\n"
                "2️⃣ Hablar con un asesor\n"
                "3️⃣ Ya soy cliente Movistar"
            )
        else:
            return "Por favor responde con *1*, *2* o *3*. 😊"

    # ── RECOPILANDO DATOS DEL CLIENTE ──
    elif estado == "recopilando_datos":
        conversaciones[numero]["nombre"] = mensaje
        conversaciones[numero]["estado"] = "recopilando_distrito"
        return f"Perfecto, *{mensaje}*! 😊\n\n¿En qué *distrito* te encuentras?"

    elif estado == "recopilando_distrito":
        conversaciones[numero]["distrito"] = mensaje
        conversaciones[numero]["estado"] = "recopilando_dni"
        return "Anotado! 📍\n\n¿Cuál es tu *número de DNI*?"

    elif estado == "recopilando_dni":
        conversaciones[numero]["dni"] = mensaje
        datos = conversaciones[numero]
        resumen = (
            f"Nombre: {datos.get('nombre')}\n"
            f"Distrito: {datos.get('distrito')}\n"
            f"DNI: {datos.get('dni')}\n"
            f"Plan: {datos.get('plan_seleccionado')}\n"
            f"WhatsApp: {numero}"
        )
        notificar_lead(numero, f"NUEVO LEAD COMPLETO:\n{resumen}")
        conversaciones[numero]["estado"] = "finalizado"
        return (
            "✅ ¡Listo! Tus datos han sido registrados correctamente.\n\n"
            f"📋 *Resumen de tu solicitud:*\n"
            f"👤 Nombre: {datos.get('nombre')}\n"
            f"📍 Distrito: {datos.get('distrito')}\n"
            f"📦 Plan: {datos.get('plan_seleccionado')}\n\n"
            "Un asesor se comunicará contigo en las próximas *2 horas* para confirmar tu instalación. 🏠\n\n"
            "¡Gracias por elegir Movistar! 💙\n\n"
            "Escribe *menu* si necesitas algo más."
        )

    # ── CLIENTE EXISTENTE ──
    elif estado == "cliente_existente":
        if msg in ["1", "2", "3"]:
            notificar_lead(numero, f"Cliente existente - opción: {msg}")
            return (
                "Entendido 👍 Un asesor especializado te contactará pronto para ayudarte.\n\n"
                "Escribe *menu* para volver al inicio."
            )
        else:
            return "Por favor responde con *1*, *2* o *3*."

    # ── ESTADO DESCONOCIDO ──
    else:
        conversaciones[numero] = {"estado": "menu"}
        return (
            "Hola de nuevo! 👋 Escribe *menu* para ver las opciones disponibles."
        )


def notificar_lead(numero_cliente, info):
    """Envía notificación a tu número cuando hay un lead."""
    enviar_mensaje(
        TU_NUMERO,
        f"🔔 *NUEVO LEAD*\n📱 Cliente: {numero_cliente}\n\n{info}"
    )


def enviar_mensaje(numero, texto):
    """Envía un mensaje de WhatsApp via Meta API."""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers=headers, json=payload)


# ──────────────────────────────────────────────
# WEBHOOK DE WHATSAPP
# ──────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    """Meta verifica el webhook con esta ruta."""
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token inválido", 403


@app.route("/webhook", methods=["POST"])
def recibir_mensaje():
    """Recibe y responde mensajes entrantes."""
    data = request.get_json()
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        mensaje_obj = entry["messages"][0]
        numero = mensaje_obj["from"]
        texto = mensaje_obj["text"]["body"]

        respuesta = obtener_respuesta(numero, texto)
        enviar_mensaje(numero, respuesta)
    except (KeyError, IndexError):
        pass  # Ignorar notificaciones que no son mensajes

    return "OK", 200


# ──────────────────────────────────────────────
# INICIAR SERVIDOR
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(port=5000, debug=True)
