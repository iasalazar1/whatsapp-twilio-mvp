# Ahorita IA · MVP Agente Virtual de WhatsApp

Prototipo de agente virtual para PyMEs mexicanas, enfocado en agendamiento de citas por WhatsApp, con evolución futura a audio y transcripción.

---

## 1. Visión del proyecto

Construir una microempresa de agentes virtuales para PyMEs en México, enfocada inicialmente en:

- clínicas dentales
- consultorios médicos
- estéticas
- barberías
- talleres con agenda

Hipótesis principal:

> Muchas PyMEs en México pierden ventas por no atender bien WhatsApp.  
> Un agente virtual que reciba texto y audio puede capturar solicitudes 24/7 con bajo costo.

---

## 2. Caso de uso del MVP

**AgentCitas WhatsApp MX**

- canal: WhatsApp
- entrada: texto
- fase nueva: audio entrante detectado, persistido y preparado para transcripción
- salida: texto
- objetivo: capturar solicitudes de cita
- datos a recolectar:
  - servicio
  - fecha
  - hora
  - nombre

---

## 3. Stack técnico actual

- Python 3
- FastAPI
- Uvicorn
- Twilio SDK
- python-dotenv
- python-multipart
- requests
- SQLite
- ngrok
- Linux Mint
- entorno virtual venv
- ffmpeg

Dependencias instaladas:

- fastapi
- uvicorn[standard]
- python-dotenv
- twilio
- python-multipart
- requests

Notas:
- `faster-whisper` se evaluó pero no fue viable localmente por limitación de CPU/NumPy
- `openai-whisper` también resultó poco conveniente en esta laptop
- por ahora se usa stub local de transcripción
- en pruebas offline con `curl`, algunos acentos pueden llegar mal codificados desde terminal
- para validar rápido el flujo local, conviene usar entradas sin acento como `manana`

---

## 4. Variables de entorno

Este proyecto usa un archivo local `.env` que **no debe subirse** al repositorio.

Referencia mínima en `.env.example`:

```env
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_twilio_auth_token
APP_ENV=local
