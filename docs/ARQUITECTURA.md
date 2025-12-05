# Arquitectura Técnica - Sistema Domótico IoT

Documentación técnica completa de la arquitectura, protocolos, flujos de datos y diseño del sistema.

---

## Índice

1. [Diagrama de Arquitectura General](#diagrama-de-arquitectura-general)
2. [Componentes del Sistema](#componentes-del-sistema)
3. [Modelo de Datos](#modelo-de-datos)
4. [Protocolo TCP](#protocolo-tcp)
5. [API REST](#api-rest)
6. [Chatbot IA Gemini](#chatbot-ia-gemini)
7. [Broadcast UDP](#broadcast-udp)
8. [Concurrencia y Threading](#concurrencia-y-threading)
9. [Flujos de Datos](#flujos-de-datos)
10. [Seguridad](#seguridad)

---

## Diagrama de Arquitectura General

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INTERFACES DE USUARIO                              │
├────────────────┬─────────────────┬─────────────────┬────────────────────────────┤
│                │                 │                 │                            │
│  Cliente CLI   │  Web Dashboard  │  Simulador 3D   │     UDP Listener           │
│  (Terminal)    │  (Navegador)    │  (React+Three)  │    (Telemetría)            │
│                │                 │                 │                            │
│ ┌────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │    ┌─────────────┐         │
│ │ Python     │ │ │ HTML/CSS/JS │ │ │ TypeScript  │ │    │ Python      │         │
│ │ Socket TCP │ │ │ Fetch API   │ │ │ Fetch API   │ │    │ Socket UDP  │         │
│ │            │ │ │ WebSpeech   │ │ │ Three.js    │ │    │             │         │
│ └──────┬─────┘ │ └──────┬──────┘ │ └──────┬──────┘ │    └──────┬──────┘         │
│        │       │        │        │        │        │           │                │
│        │       │    ┌───┴───┐    │        │        │           │                │
│        │       │    │Chatbot│    │        │        │           │                │
│        │       │    │Jarvis │    │        │        │           │                │
│        │       │    │🎤 🤖 │    │        │        │           │                │
│        │       │    └───┬───┘    │        │        │           │                │
└────────┼───────┴────────┼────────┴────────┼────────┴───────────┼────────────────┘
         │                │ HTTP :8080      │                    │
         │ TCP :5000      │ + /api/chat     │ HTTP :8080         │ UDP :5001
         │                │ HTTP :8000      │ HTTP :3000         │ (broadcast)
         ▼                ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     SERVIDOR CENTRAL (server_domotico.py)                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│    ┌──────────────────────────────────────────────────────────────────────┐     │
│    │                    DomoticServer (Orquestador)                       │     │
│    │                         main thread                                  │     │
│    └────────────┬─────────────────┬─────────────────┬─────────────────────┘     │
│                 │                 │                 │                           │
│    ┌────────────▼────────┐ ┌──────▼──────────┐ ┌────▼───────────────┐           │
│    │    TCPServer        │ │   Flask API     │ │  UDPBroadcaster    │           │
│    │   (Puerto 5000)     │ │  (Puerto 8080)  │ │   (Puerto 5001)    │           │
│    │                     │ │                 │ │                    │           │
│    │ • socket.listen()   │ │ • REST Endpoints│ │ • Broadcast c/2s   │           │
│    │ • Multi-cliente     │ │ • /api/chat     │ │ • JSON telemetría  │           │
│    │ • Threading         │ │ • Gemini AI     │ │ • SO_BROADCAST     │           │
│    │ • Protocolo texto   │ │ • CORS enabled  │ │                    │           │
│    └──────────┬──────────┘ └────────┬────────┘ └─────────┬──────────┘           │
│               │                     │                    │                      │
│               └─────────────────────┼────────────────────┘                      │
│                                     │                                           │
│                          ┌──────────▼──────────┐                                │
│                          │   DeviceManager     │                                │
│                          │  (Lógica Central)   │                                │
│                          ├─────────────────────┤                                │
│                          │ • threading.Lock    │◄── Thread-Safe                 │
│                          │ • devices: Dict     │                                │
│                          │ • log: List[str]    │                                │
│                          │ • Timers auto-off   │                                │
│                          └──────────┬──────────┘                                │
│                                     │                                           │
│                          ┌──────────▼──────────┐                                │
│                          │   Device Model      │                                │
│                          ├─────────────────────┤                                │
│                          │ • id: str           │                                │
│                          │ • type: str         │   Tipos:                       │
│                          │ • estado: str       │   - luz                        │
│                          │ • auto_off: int     │   - enchufe                    │
│                          │ • brightness: int   │   - cortinas                   │
│                          │ • color: str        │   - termostato                 │
│                          │ • curtains: int     │                                │
│                          │ • temperature: float│                                │
│                          │ • target_temp: float│                                │
│                          └─────────────────────┘                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Nota:** Para facilitar el uso de la interfaz web, el simulador 3D se aloja en un servidor en el puerto 3000, y se accede a la web desde un servidor en el puerto 8000.

---

## Componentes del Sistema

### 1. DomoticServer (Orquestador)

Clase principal que inicializa y coordina todos los componentes:

```python
class DomoticServer:
    def __init__(self):
        self.device_manager = DeviceManager()      # Lógica central
        self.tcp_server = TCPServer(...)           # Comandos TCP
        self.udp_broadcaster = UDPBroadcaster(...) # Telemetría
        self.flask_app = create_api(...)           # REST + Gemini
    
    def start(self):
        # Inicia todos los servicios en threads separados
        tcp_thread.start()
        udp_thread.start()
        flask_thread.start()
```

### 2. DeviceManager (Lógica de Negocio)

Gestiona el estado de todos los dispositivos de forma thread-safe:

```python
class DeviceManager:
    def __init__(self):
        self.lock = threading.Lock()  # Protección concurrente
        self.devices = {
            'luz_salon': Device('luz_salon', 'luz'),
            'enchufe_tv': Device('enchufe_tv', 'enchufe'),
            'enchufe_calefactor': Device('enchufe_calefactor', 'enchufe'),
            'cortinas': Device('cortinas', 'cortinas'),
            'termostato': Device('termostato', 'termostato')
        }
        self.log = []  # Últimas 100 entradas
```

**Métodos principales:**

| Método | Descripción |
|--------|-------------|
| `set_device_state(id, ON/OFF)` | Encender/Apagar dispositivo |
| `set_brightness(id, 0-100)` | Ajustar brillo de luz |
| `set_color(id, #RRGGBB)` | Cambiar color de luz |
| `set_curtains(0-100)` | Posición de cortinas |
| `set_temperature(16-30)` | Temperatura objetivo |
| `set_auto_off(id, segundos)` | Programar auto-apagado |
| `get_all_devices()` | Obtener estado de todos |

### 3. TCPServer (Comandos)

Servidor TCP multi-cliente para comandos de control:

```python
class TCPServer:
    def _run(self):
        self.socket.bind((host, 5000))
        self.socket.listen(5)
        
        while running:
            client, addr = self.socket.accept()
            # Nuevo thread por cliente
            threading.Thread(target=self._handle_client, args=(client,)).start()
```

### 4. Flask API (REST + Gemini)

API REST con integración de chatbot IA:

```python
def create_api(device_manager):
    app = Flask(__name__)
    CORS(app)  # Permite requests desde navegador
    
    @app.route('/api/status')
    def get_status():
        return jsonify(device_manager.get_all_devices())
    
    @app.route('/api/chat', methods=['POST'])
    def chat_with_gemini():
        # Procesa mensaje con IA y ejecuta acciones
        ...
```

### 5. UDPBroadcaster (Telemetría)

Emisor de estado broadcast cada 2 segundos:

```python
class UDPBroadcaster:
    def _run(self):
        sock = socket.socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        
        while running:
            payload = json.dumps({
                'timestamp': datetime.now().isoformat(),
                'devices': device_manager.get_all_devices()
            })
            sock.sendto(payload.encode(), ('<broadcast>', 5001))
            time.sleep(2)
```

---

## Modelo de Datos

### Clase Device

```python
class Device:
    def __init__(self, device_id: str, device_type: str):
        self.id = device_id              # Identificador único
        self.type = device_type          # 'luz', 'enchufe', 'cortinas', 'termostato'
        
        # Estado según tipo
        if device_type in ['cortinas', 'termostato']:
            self.estado = 'N/A'          # No tienen ON/OFF
            self.auto_off = 0            # No aplica
        else:
            self.estado = 'OFF'          # ON/OFF
            self.auto_off = 0            # Segundos para auto-apagado
        
        self.ultimo_cambio = datetime.now().isoformat()
        self.auto_off_timer = None       # threading.Timer activo
        
        # Parámetros específicos por tipo
        self.brightness = 40 if device_type == 'luz' else 0
        self.color = '#ffffff' if device_type == 'luz' else '#000000'
        self.curtains = 50 if device_type == 'cortinas' else 0
        self.temperature = 19 if device_type == 'termostato' else 0
        self.target_temperature = 21 if device_type == 'termostato' else 0
```

### Tipos de Dispositivos

| Tipo | Estado | Auto-Off | Parámetros Específicos |
|------|--------|----------|------------------------|
| `luz` | ON/OFF | ✅ Sí | brightness (0-100), color (#RRGGBB) |
| `enchufe` | ON/OFF | ✅ Sí | - |
| `cortinas` | N/A | ❌ No | curtains (0-100% posición) |
| `termostato` | N/A | ❌ No | temperature, target_temperature |

### Dispositivos Registrados

| ID | Tipo | Descripción |
|----|------|-------------|
| `luz_salon` | luz | Luz principal del salón |
| `enchufe_tv` | enchufe | Smart plug para televisor |
| `enchufe_calefactor` | enchufe | Smart plug para calefactor |
| `cortinas` | cortinas | Sistema de cortinas motorizadas |
| `termostato` | termostato | Control de climatización |

---

## Protocolo TCP

### Formato de Mensajes

```
Cliente → Servidor:  "COMANDO param1 param2\n"
Servidor → Cliente:  "OK resultado\n" o "ERROR mensaje\n"
```

### Tabla de Comandos

| Comando | Sintaxis | Auth | Descripción |
|---------|----------|:----:|-------------|
| `LOGIN` | `LOGIN <user> <pass>` | ❌ | Autenticación de usuario |
| `LIST` | `LIST` | ❌ | Listar todos los dispositivos |
| `STATUS` | `STATUS <device_id>` | ❌ | Estado de un dispositivo |
| `SET` | `SET <id> <subcomando> [valor]` | ✅ | Controlar dispositivo |
| `AUTO_OFF` | `AUTO_OFF <id> <segundos>` | ✅ | Programar auto-apagado |
| `LOG` | `LOG` | ❌ | Ver historial de eventos |
| `EXIT` | `EXIT` | ❌ | Cerrar conexión |

### Subcomandos SET

| Subcomando | Sintaxis | Dispositivos | Rango |
|------------|----------|--------------|-------|
| `ON` | `SET <id> ON` | luz, enchufe | - |
| `OFF` | `SET <id> OFF` | luz, enchufe | - |
| `BRIGHTNESS` | `SET <id> BRIGHTNESS <valor>` | luz | 0-100 |
| `COLOR` | `SET <id> COLOR <hex>` | luz | #000000-#FFFFFF |
| `LEVEL` | `SET cortinas LEVEL <valor>` | cortinas | 0-100 |
| `TEMP` | `SET termostato TEMP <valor>` | termostato | 16-30 |

### Ejemplo de Sesión Completa

```text
Conexión establecida...
< SERVIDOR DOMOTICO v1.0
< Comandos: LOGIN, LIST, STATUS, SET, AUTO_OFF, LOG, EXIT

> LOGIN admin admin123
< OK LOGIN Bienvenido admin

> LIST
< OK 5 luz_salon,OFF,0,40,#ffffff,0,0,0;enchufe_tv,OFF,0,0,#000000,0,0,0;...

> SET luz_salon ON
< OK SET luz_salon ON

> SET luz_salon BRIGHTNESS 75
< OK SET luz_salon BRIGHTNESS 75

> SET luz_salon COLOR #ff6600
< OK SET luz_salon COLOR #ff6600

> SET cortinas LEVEL 80
< OK SET cortinas LEVEL 80

> SET termostato TEMP 22
< OK SET termostato TEMP 22.0

> AUTO_OFF luz_salon 60
< OK AUTO_OFF luz_salon 60

> STATUS luz_salon
< OK STATUS luz_salon,ON,60,75,#ff6600,0,0,0

> LOG
< OK LOG [2025-11-27 10:30:00] luz_salon: Estado cambiado a ON; ...

> EXIT
< OK EXIT Hasta luego!
```

### Códigos de Error

| Error | Causa |
|-------|-------|
| `ERROR LOGIN: Credenciales inválidas` | Usuario o contraseña incorrectos |
| `ERROR SET: Requiere autenticación` | Comando sin LOGIN previo |
| `ERROR SET: Dispositivo no encontrado` | ID de dispositivo inválido |
| `ERROR SET: Subcomando no válido` | Subcomando no reconocido |
| `ERROR: Comando no reconocido` | Comando desconocido |

---

## API REST

### Endpoints Completos

| Método | Endpoint | Body JSON | Respuesta |
|--------|----------|-----------|-----------|
| GET | `/api/status` | - | Lista de todos los dispositivos |
| GET | `/api/device/<id>` | - | Estado de un dispositivo |
| POST | `/api/control` | `{id, action}` | Resultado ON/OFF |
| POST | `/api/brightness` | `{id, brightness}` | Confirmación |
| POST | `/api/color` | `{id, color}` | Confirmación |
| POST | `/api/curtains` | `{position}` | Confirmación |
| POST | `/api/temperature` | `{temperature}` | Confirmación |
| POST | `/api/auto_off` | `{id, seconds}` | Confirmación |
| POST | `/api/chat` | `{message}` | Respuesta IA + acciones |
| GET | `/api/log` | - | Historial de eventos |

### Ejemplos de Peticiones y Respuestas

#### GET /api/status

**Respuesta:**

```json
{
  "success": true,
  "timestamp": "2025-11-27T10:30:00.123456",
  "total": 5,
  "devices": [
    {
      "id": "luz_salon",
      "type": "luz",
      "estado": "ON",
      "auto_off": 0,
      "brightness": 75,
      "color": "#ff6600",
      "curtains": 0,
      "temperature": 0,
      "target_temperature": 0,
      "ultimo_cambio": "2025-11-27T10:25:00.000000"
    },
    ...
  ]
}
```

#### POST /api/control

**Request:**

```json
{
  "id": "luz_salon",
  "action": "ON"
}
```

**Response:**

```json
{
  "success": true,
  "device_id": "luz_salon",
  "new_state": "ON"
}
```

#### POST /api/chat

**Request:**

```json
{
  "message": "Activa el modo cine"
}
```

**Response:**

```json
{
  "success": true,
  "response": "Modo cine activado: luces tenues azules, cortinas cerradas y TV encendida.",
  "actions": [
    "luz_salon -> Brillo 10%",
    "luz_salon -> Color #0000ff",
    "Cortinas -> 0%",
    "enchufe_tv -> ON"
  ]
}
```

---

## Chatbot IA Gemini

### Arquitectura del Chatbot

```text
┌─────────────────────────────────────────────────────────────────┐
│                    CHATBOT JARVIS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │  Dashboard  │      │  Flask API  │      │   Gemini    │     │
│  │  (Browser)  │─────►│  /api/chat  │─────►│   2.5 Flash │     │
│  │             │      │             │      │             │     │
│  │ 🎤 Voz      │      │             │      │             │     │
│  │ ⌨️ Texto    │      └──────┬──────┘      └──────┬──────┘     │
│  └─────────────┘             │                    │             │
│                              ▼                    │             │
│                    ┌─────────────────┐            │             │
│                    │  Contexto       │            │             │
│                    │  Estado actual  │◄───────────┘             │
│                    │  de dispositivos│   Respuesta JSON         │
│                    └────────┬────────┘   con acciones           │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                          │
│                    │ DeviceManager   │                          │
│                    │ Ejecuta acciones│                          │
│                    └─────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Procesamiento

1. **Usuario** envía mensaje (texto o voz)
2. **Dashboard** captura con Web Speech API (si es voz)
3. **POST /api/chat** con el mensaje
4. **Servidor** construye contexto con estado actual
5. **Gemini** procesa y genera respuesta JSON
6. **Servidor** parsea acciones y las ejecuta
7. **Respuesta** con texto + lista de acciones ejecutadas

### Prompt del Sistema

```python
context = f"""
Estado actual de la habitación:
- Luz del salón: {estado}, Brillo: {brightness}%, Color: {color}
- TV: {tv_estado}
- Calefactor: {calef_estado}
- Cortinas: {curtains}% abiertas
- Temperatura actual: {temp}°C, Objetivo: {target_temp}°C

Eres Jarvis, un asistente de domótica inteligente. Responde de forma breve.
Cuando el usuario pida controlar algo, responde con JSON:
{{"actions": [...], "response": "mensaje"}}

Dispositivos y acciones disponibles:
- luz_salon: ON, OFF, BRIGHTNESS (0-100), COLOR (#RRGGBB)
- enchufe_tv: ON, OFF
- enchufe_calefactor: ON, OFF  
- cortinas: LEVEL (0-100)
- termostato: TEMP (16-30)
"""
```

### Comandos Especiales Reconocidos

| Comando | Acciones Ejecutadas |
|---------|---------------------|
| "Modo cine" | Brillo 10%, Color azul, Cortinas 0%, TV ON |
| "Hace frío" | Temperatura +3°C, Calefactor ON |
| "Buenos días" | Luz ON, Cortinas 100%, Brillo 80% |
| "Buenas noches" | Todo OFF, Cortinas 0% |

### Reconocimiento de Voz

```javascript
// Web Speech API (Chrome/Edge)
const recognition = new webkitSpeechRecognition();
recognition.lang = 'es-ES';
recognition.continuous = false;

recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    sendChatMessage(transcript);
};
```

---

## Broadcast UDP

### Características

- **Puerto**: 5001
- **Intervalo**: Cada 2 segundos
- **Formato**: JSON
- **Dirección**: Broadcast (`<broadcast>`)
- **Protocolo**: UDP (sin conexión)

### Estructura del Paquete

```json
{
  "timestamp": "2025-11-27T10:30:00.123456",
  "devices": [
    {
      "id": "luz_salon",
      "type": "luz",
      "estado": "ON",
      "auto_off": 0,
      "brightness": 75,
      "color": "#ff6600",
      "curtains": 0,
      "temperature": 0,
      "target_temperature": 0,
      "ultimo_cambio": "2025-11-27T10:25:00.000000"
    },
    ...
  ]
}
```

### Receptor UDP (udp_listener.py)

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', 5001))

while True:
    data, addr = sock.recvfrom(4096)
    telemetry = json.loads(data.decode())
    print_table(telemetry['devices'])
```

---

## Concurrencia y Threading

### Mapa de Threads

```text
Main Thread (DomoticServer.start)
│
├── TCPServer Thread
│   ├── Cliente Thread 1 (handle_client)
│   ├── Cliente Thread 2 (handle_client)
│   └── Cliente Thread N...
│
├── UDPBroadcaster Thread (broadcast loop)
│
├── Flask API Thread (werkzeug server)
│
└── Auto-off Timer Threads (dinámicos)
    ├── Timer luz_salon (60s)
    └── Timer enchufe_tv (30s)
```

### Protección con Lock

```python
class DeviceManager:
    def __init__(self):
        self.lock = threading.Lock()
    
    def set_device_state(self, device_id, new_state):
        with self.lock:  # Exclusión mutua
            device = self.devices.get(device_id)
            device.estado = new_state
            # Operación atómica protegida
```

**Protege contra:**

- Race conditions
- Corrupción de datos
- Conflictos timer vs comando manual

### Gestión de Timers

```python
def set_auto_off(self, device_id, segundos):
    with self.lock:
        device = self.devices.get(device_id)
        
        # Cancelar timer anterior
        if device.auto_off_timer:
            device.auto_off_timer.cancel()
        
        device.auto_off = segundos
        
        if segundos > 0:
            timer = threading.Timer(
                segundos,
                self._auto_off_callback,
                args=[device_id]
            )
            timer.daemon = True  # No bloquea cierre
            timer.start()
            device.auto_off_timer = timer
```

---

## Flujos de Datos

### Flujo 1: Control desde CLI

```text
Cliente CLI              TCPServer              DeviceManager
    │                        │                       │
    │ SET luz_salon ON       │                       │
    ├───────────────────────►│                       │
    │                        │ set_device_state()    │
    │                        ├──────────────────────►│
    │                        │                       │ Lock.acquire()
    │                        │                       │ device.estado = 'ON'
    │                        │                       │ timestamp = now()
    │                        │                       │ _add_log(...)
    │                        │                       │ Lock.release()
    │                        │◄──────────────────────┤
    │ OK SET luz_salon ON    │                       │
    │◄───────────────────────┤                       │
```

### Flujo 2: Control desde Dashboard Web

```text
Dashboard              Flask API              DeviceManager
    │                      │                       │
    │ POST /api/control    │                       │
    │ {id, action: ON}     │                       │
    ├─────────────────────►│                       │
    │                      │ set_device_state()    │
    │                      ├──────────────────────►│
    │                      │                       │ (mismo proceso)
    │                      │◄──────────────────────┤
    │ {success: true}      │                       │
    │◄─────────────────────┤                       │
    │                      │                       │
    │ GET /api/status      │                       │
    ├─────────────────────►│ get_all_devices()     │
    │                      ├──────────────────────►│
    │ [dispositivos]       │◄──────────────────────┤
    │◄─────────────────────┤                       │
```

### Flujo 3: Chatbot con IA

```text
Dashboard          Flask /chat          Gemini AI         DeviceManager
    │                  │                    │                   │
    │ "Modo cine"      │                    │                   │
    ├─────────────────►│                    │                   │
    │                  │ get_all_devices()  │                   │
    │                  ├────────────────────┼──────────────────►│
    │                  │◄───────────────────┼───────────────────┤
    │                  │                    │                   │
    │                  │ generate_content() │                   │
    │                  ├───────────────────►│                   │
    │                  │ JSON con acciones  │                   │
    │                  │◄───────────────────┤                   │
    │                  │                    │                   │
    │                  │ Ejecutar acciones  │                   │
    │                  ├────────────────────┼──────────────────►│
    │                  │◄───────────────────┼───────────────────┤
    │                  │                    │                   │
    │ {response, actions}                   │                   │
    │◄─────────────────┤                    │                   │
```

### Flujo 4: Auto-apagado

```text
Cliente              DeviceManager             Timer Thread
    │                      │                        │
    │ AUTO_OFF luz 30      │                        │
    ├─────────────────────►│                        │
    │                      │ Timer(30s).start() ───►│
    │ OK                   │                        │
    │◄─────────────────────┤                        │
    │                      │                        │
    │        [30 segundos después...]               │
    │                      │                        │
    │                      │◄─────── callback() ────┤
    │                      │ Lock.acquire()         │
    │                      │ estado = 'OFF'         │
    │                      │ auto_off = 0           │
    │                      │ _add_log("Auto-off")   │
    │                      │ Lock.release()         │
```

---

## Seguridad

### Limitaciones Actuales (Desarrollo)

| Aspecto | Estado | Riesgo |
|---------|--------|--------|
| Autenticación | Hardcoded | ⚠️ Alto |
| Contraseñas | Texto plano | ⚠️ Alto |
| Cifrado TCP | Ninguno | ⚠️ Alto |
| HTTPS | No | ⚠️ Medio |
| CORS | Permisivo (*) | ⚠️ Medio |
| Rate Limiting | No | ⚠️ Bajo |

### Mejoras para Producción

```python
# 1. Hashing de contraseñas
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 2. JWT para sesiones
import jwt
token = jwt.encode({'user': username, 'exp': datetime.utcnow() + timedelta(hours=1)}, SECRET_KEY)

# 3. HTTPS
# Usar nginx como reverse proxy con certificado SSL

# 4. Rate limiting
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/control')
@limiter.limit("10 per minute")
def control():
    ...
```

---

## Puertos y Servicios

| Puerto | Protocolo | Servicio | Descripción |
|--------|-----------|----------|-------------|
| 5000 | TCP | TCPServer | Comandos de control |
| 5001 | UDP | Broadcaster | Telemetría (broadcast) |
| 8080 | HTTP | Flask API | REST + Chatbot |
| 3000 | HTTP | Vite | Simulador 3D (desarrollo) |

---

## Patrones de Diseño

| Patrón | Implementación |
|--------|----------------|
| **Singleton** | DeviceManager compartido |
| **Factory** | `create_api()` para Flask |
| **Observer** | UDP broadcast |
| **Thread Pool** | Clientes TCP concurrentes |
| **MVC** | Model (Device) / View (Web) / Controller (Manager) |
| **Mediator** | DomoticServer coordina componentes |

---

## Testing

### Suite de Pruebas (`test_sistema.py`)

```python
# Ejecutar:
python scripts/test_sistema.py
```

**Tests incluidos:**

| Categoría | Tests |
|-----------|-------|
| Conexión TCP | Conexión, desconexión, timeout |
| Comandos | LOGIN, LIST, STATUS, SET, AUTO_OFF, LOG |
| Autenticación | Login válido/inválido, protección comandos |
| API REST | Todos los endpoints |
| Concurrencia | Múltiples clientes simultáneos |
| Auto-off | Creación, cancelación, ejecución |

---

## Escalabilidad

### Limitaciones Actuales

- 5 dispositivos fijos (hardcoded)
- Estado solo en memoria
- Servidor único (no distribuido)

### Mejoras Posibles

| Mejora | Tecnología |
|--------|------------|
| Persistencia | SQLite / PostgreSQL |
| Configuración dinámica | JSON/YAML config file |
| Caché distribuida | Redis |
| Múltiples instancias | Load balancer + Redis |
| Mensajería | RabbitMQ / Kafka |
| Containerización | Docker + Docker Compose |

---

## Fin de la Documentación Técnica
