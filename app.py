from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Almacenamiento temporal de sesiones de usuarios
# En producción, usa una base de datos
user_sessions = {}

PREGUNTAS = [
    "¿Qué tan alta está el agua?\n1️⃣ En el piso\n2️⃣ Tobillo\n3️⃣ Canilla\n4️⃣ Rodilla\n5️⃣ Cadera",
    "¿Qué tan rápido subió el nivel del agua?\n1️⃣ 2+ horas\n2️⃣ 1 hora\n3️⃣ 30 minutos\n4️⃣ 15 minutos\n5️⃣ Menos de 15 minutos",
    "¿Está usted sol@?\n1️⃣ No\n2️⃣ Sí",
    "¿Qué tanto llueve en este momento?\n1️⃣ No llueve\n2️⃣ Llovizna\n3️⃣ Lluvia leve\n4️⃣ Lluvia fuerte\n5️⃣ Tormenta",
    "¿Cuál es el nivel del agua afuera de su casa?\n1️⃣ Piso\n2️⃣ Tobillo\n3️⃣ Canilla\n4️⃣ Rodilla\n5️⃣ Cadera"
]

UMBRAL_ATENCION = 15

MENSAJE_NO_URGENTE = ("Gracias por tu reporte. Según la información que nos compartes, "
                      "la situación no parece requerir una atención urgente en este momento. "
                      "Te sugerimos buscar apoyo con tus vecinos o comunicarte con las autoridades "
                      "locales cercanas. Si la situación cambia o se agrava, por favor vuelve a "
                      "reportarlo para que podamos ayudarte mejor.")

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    """Maneja los mensajes entrantes de WhatsApp"""
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # Inicializar sesión si no existe
    if from_number not in user_sessions:
        user_sessions[from_number] = {
            'estado': 'inicio',
            'respuestas': [],
            'puntos': 0
        }
    
    session = user_sessions[from_number]
    
    # Estado: Inicio
    if session['estado'] == 'inicio':
        msg.body("¡Hola! ¿En qué puedo ayudarte hoy?\n\n1️⃣ Solicitar ayuda con una inundación\n2️⃣ Cancelar")
        session['estado'] = 'menu_principal'
    
    # Estado: Menú principal
    elif session['estado'] == 'menu_principal':
        if incoming_msg == '1':
            session['estado'] = 'pregunta_0'
            msg.body(PREGUNTAS[0])
        elif incoming_msg == '2':
            msg.body("Que tengas un excelente día.")
            del user_sessions[from_number]
        else:
            msg.body("Por favor selecciona 1 o 2.\n\n1️⃣ Solicitar ayuda con una inundación\n2️⃣ Cancelar")
    
    # Estados: Preguntas 0-4
    elif session['estado'].startswith('pregunta_'):
        numero_pregunta = int(session['estado'].split('_')[1])
        
        # Validar respuesta
        if not incoming_msg.isdigit():
            msg.body(f"Por favor responde con un número.\n\n{PREGUNTAS[numero_pregunta]}")
            return str(resp)
        
        respuesta = int(incoming_msg)
        
        # Validar rango según la pregunta
        max_valor = 2 if numero_pregunta == 2 else 5  # Pregunta 3 solo tiene opciones 1 y 2
        
        if respuesta < 1 or respuesta > max_valor:
            msg.body(f"Por favor selecciona una opción válida (1-{max_valor}).\n\n{PREGUNTAS[numero_pregunta]}")
            return str(resp)
        
        # Guardar respuesta y sumar puntos
        session['respuestas'].append(respuesta)
        session['puntos'] += respuesta
        
        # Siguiente pregunta o resultado final
        if numero_pregunta < 4:
            session['estado'] = f'pregunta_{numero_pregunta + 1}'
            msg.body(PREGUNTAS[numero_pregunta + 1])
        else:
            # Evaluar resultado final
            puntos_totales = session['puntos']
            
            if puntos_totales >= UMBRAL_ATENCION:
                msg.body(f"⚠️ *SITUACIÓN URGENTE DETECTADA*\n\n"
                        f"Tu evaluación arroja {puntos_totales}/25 puntos.\n\n"
                        f"Un asesor humano se comunicará contigo lo antes posible. "
                        f"Mantente en un lugar seguro y alto.\n\n"
                        f"📞 Si es una emergencia extrema, llama al 123.")
            else:
                msg.body(f"Evaluación completada \n\n{MENSAJE_NO_URGENTE}")
            
            # Limpiar sesión
            del user_sessions[from_number]
    
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
