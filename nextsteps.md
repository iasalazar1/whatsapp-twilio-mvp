
---

# `NEXTSTEPS.md`

```md
# NEXT STEPS

## Estado actual resumido

El MVP ya tiene:

- backend funcional con FastAPI
- webhook `/whatsapp`
- persistencia con SQLite
- flujo conversacional con estados
- logs y rutas debug
- soporte de media entrante
- descarga real de media validada con Twilio Sandbox
- stub local de transcripción
- validaciones básicas endurecidas en:
  - servicio
  - fecha
  - hora
  - nombre

---

## Bloque recién cerrado

### Flujo conversacional endurecido
Se mejoró el flujo para evitar que avance con entradas basura o ambiguas.

Validaciones agregadas:
- servicio inválido no avanza
- fecha inválida no avanza
- hora inválida no avanza
- nombre incompleto no cierra la cita

### Media real validada
Se confirmó que:
- Twilio envía media real al webhook
- el backend la detecta
- el archivo se descarga localmente
- el registro queda persistido en `mediafiles`

---

## Siguiente bloque recomendado

## 1. Parsing básico de fecha y hora

Objetivo:
guardar valores más consistentes sin meter todavía IA ni servicios de nube.

### Alcance mínimo sugerido
- reconocer y normalizar:
  - `manana` / `mañana`
  - `hoy`
  - días de semana como `viernes`
- normalizar horas como:
  - `5 pm`
  - `10:30 am`
  - `16:00`

### Qué sí hacer
- mantener reglas simples
- no romper el flujo actual
- seguir probando offline con `curl`

### Qué no hacer todavía
- resolver agenda real con calendario
- timezone complejo
- interpretación avanzada de lenguaje natural

---

## Pendientes posteriores

## 2. Transcripción real en nube
Objetivo:
reemplazar el stub local por una integración real de transcripción en nube cuando ya aporte valor claro.

## 3. Multi-negocio
Objetivo:
preparar la base para usar el mismo motor con distintas PyMEs y configuraciones.

## 4. Despliegue productivo
Objetivo:
mover el MVP de entorno local a una primera versión utilizable en producción controlada.

---

## Orden recomendado

1. parsing básico de fecha y hora
2. evaluar si conviene mejorar stub/transcripción
3. transcripción real en nube
4. multi-negocio
5. despliegue productivo

---

## Reglas de trabajo

- respuestas y cambios breves
- paso a paso
- validar cada cambio antes del siguiente
- priorizar offline
- no cambiar el plan salvo justificación clara
- evitar sobreingeniería

---

## Checklist operativo antes de cada sesión

- levantar entorno local
- validar `/health`
- validar rutas `/debug/*`
- revisar que git esté limpio
- definir un solo bloque de avance por sesión
