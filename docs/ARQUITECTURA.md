# Arquitectura Técnica - Sistema Domótico IoT

Documentación técnica detallada de la arquitectura, flujos de datos y diseño del sistema.

---

## Diagrama de Componentes

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLIENTES / INTERFACES                              │
├─────────────┬───────────────┬───────────────┬───────────────────────────────┤
│             │               │               │                               │
│ Cliente CLI │ Web Dashboard │ Simulador 3D  │        UDP Listener           │
│ (Terminal)  │ (Navegador)   │ (React+Three) │       (Telemetría)            │
│             │               │               │                               │
│ ┌─────────┐ │ ┌───────────┐ │ ┌───────────┐ │       ┌───────────┐           │
│ │ Python  │ │ │ HTML/CSS  │ │ │ TypeScript│ │       │ Python    │           │
│ │ Socket  │ │ │ JavaScript│ │ │ Fetch API │ │       │ Socket    │           │
│ │ TCP     │ │ │ Fetch API │ │ │ Vite      │ │       │ UDP       │           │
│ └─────┬───┘ │ └─────┬─────┘ │ └─────┬─────┘ │       └─────┬─────┘           │
│       │     │       │       │       │       │             │                 │
└───────┼─────┴───────┼───────┴───────┼───────┴─────────────┼─────────────────┘
        │             │               │                     │
        │ TCP :5000   │ HTTP :8080    │ HTTP :8080          │ UDP :5001
        │             │               │                     │
        ▼             ▼               ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SERVIDOR CENTRAL (server_domotico.py)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   DomoticServer (Orquestador)                       │    │
│  └──────────┬──────────────────────┬─────────────────────┬─────────────┘    │
│             │                      │                     │                  │
│   ┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌────────▼────────┐         │
│   │   TCPServer       │  │   Flask API       │  │ UDPBroadcaster  │         │
│   │  (Puerto 5000)    │  │  (Puerto 8080)    │  │ (Puerto 5001)   │         │
│   │                   │  │                   │  │                 │         │
│   │ • Threading       │  │ • REST Endpoints  │  │ • Broadcast     │         │
│   │ • Socket.listen() │  │ • JSON Response   │  │ • Telemetría    │         │
│   │ • Multi-cliente   │  │ • CORS Enabled    │  │ • Cada 2s       │         │
│   └───────────────────┘  └───────────────────┘  └─────────────────┘         │
│             │                      │                      │                 │
│             └──────────────────────┼──────────────────────┘                 │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │  DeviceManager    │                              │
│                          │  (Lógica Central) │                              │
│                          ├───────────────────┤                              │
│                          │ • threading.Lock  │◄─── Thread-Safe              │
│                          │ • devices: Dict   │                              │
│                          │ • log: List       │                              │
│                          │ • Timers (auto)   │                              │
│                          └─────────┬─────────┘                              │
│                                    │                                        │
│                          ┌─────────▼─────────┐                              │
│                          │   Device Model    │                              │
│                          ├───────────────────┤                              │
│                          │ • id              │                              │
│                          │ • type (luz/      │                              │
│                          │   enchufe/        │                              │
│                          │   cortinas/       │                              │ 
│                          │   termostato)     │                              │
│                          │ • estado (ON/OFF/ │                              │
│                          │   N/A)            │                              │
│                          │ • auto_off (seg)  │                              │
│                          │ • brightness      │                              │
│                          │ • color           │                              │
│                          │ • curtains        │                              │
│                          │ • temperature     │                              │
│                          │ • target_temp     │                              │
│                          └───────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Concurrencia y Threading

### Hilos del Sistema

```
Main Thread (DomoticServer.start)
├── TCPServer Thread
│   └── Cliente Thread 1
│   └── Cliente Thread 2
│   └── Cliente Thread N...
├── UDPBroadcaster Thread
├── Flask API Thread
└── Auto-off Timer Threads (dinámicos, por dispositivo)
```

### Thread-Safety con Locks

El `DeviceManager` utiliza `threading.Lock` para proteger el acceso concurrente:

```python
class DeviceManager:
    def __init__(self):
        self.lock = threading.Lock()  # Protección
        self.devices: Dict[str, Device] = {}
        self.log: List[str] = []
    
    def set_device_state(self, device_id: str, nuevo_estado: str) -> bool:
        with self.lock:  # Solo 1 thread a la vez
            # Código crítico aquí
            device = self.devices.get(device_id)
            # ...
```

**Protege contra:**

- Race conditions al leer/escribir estado
- Corrupción de datos compartidos
- Conflictos entre timers y comandos manuales

---

## Flujo de Datos - Control de Dispositivo

### Secuencia: Cliente CLI → Servidor → DeviceManager

```
Cliente CLI                   TCPServer                   DeviceManager
    │                            │                             │
    │ 1. LOGIN admin admin123    │                             │
    ├───────────────────────────►│                             │
    │                            │ Verificar USUARIOS dict     │
    │◄───────────────────────────┤                             │
    │ OK LOGIN Bienvenido admin  │                             │
    │                            │                             │
    │ 2. SET luz_salon ON        │                             │
    ├───────────────────────────►│                             │
    │                            │ 3. set_device_state()       │
    │                            ├────────────────────────────►│
    │                            │                             │ Lock.acquire()
    │                            │                             │ devices['luz_salon'].estado = 'ON'
    │                            │                             │ Cancelar timer si existe
    │                            │                             │ timestamp = now()
    │                            │                             │ _add_log(...)
    │                            │                             │ Lock.release()
    │                            │◄────────────────────────────┤
    │                            │ True (éxito)                │
    │◄───────────────────────────┤                             │
    │ OK SET luz_salon ON        │                             │
```

---

## Flujo de Autoapagado

### Secuencia: Web Dashboard → API REST → Timer

```
Web Dashboard              Flask API              DeviceManager            Timer Thread
    │                         │                         │                      │
    │ POST /api/auto_off      │                         │                      │
    │ {id, seconds:30}        │                         │                      │
    ├────────────────────────►│                         │                      │
    │                         │ set_auto_off()          │                      │
    │                         ├────────────────────────►│                      │
    │                         │                         │ Lock.acquire()       │
    │                         │                         │ Cancelar timer prev  │
    │                         │                         │ device.auto_off = 30 │
    │                         │                         │ timer = Timer(30)    │
    │                         │                         │ timer.start() ──────►│
    │                         │                         │ _add_log()           │
    │                         │                         │ Lock.release()       │
    │                         │◄────────────────────────┤                      │
    │◄────────────────────────┤                         │                      │
    │ {success: true}         │                         │                      │
    │                         │                         │                      │
    │        [Espera 30 segundos...]                    │                      │
    │                         │                         │                      │
    │                         │                         │  Timer expira        │
    │                         │                         │◄─────────────────────┤
    │                         │                         │ _auto_off_callback() │
    │                         │                         │ Lock.acquire()       │
    │                         │                         │ device.estado = 'OFF'│
    │                         │                         │ device.auto_off = 0  │
    │                         │                         │ _add_log()           │
    │                         │                         │ Lock.release()       │
```

---

## Broadcast UDP - Telemetría

### Loop del UDPBroadcaster

```python
class UDPBroadcaster:
    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            # 1. Obtener estado (thread-safe)
            devices = self.device_manager.get_all_devices()
            
            # 2. Serializar a JSON
            payload = json.dumps({
                'timestamp': datetime.now().isoformat(),
                'devices': devices
            })
            
            # 3. Broadcast a puerto 5001
            sock.sendto(payload.encode('utf-8'), ('<broadcast>', 5001))
            
            # 4. Esperar 2 segundos
            time.sleep(2)
```

**Características:**

- Unidireccional (solo envío)
- No requiere conexión
- Múltiples listeners pueden recibir simultáneamente
- Útil para monitorización pasiva

---

## Protocolo TCP Personalizado

### Formato de Mensajes

Todos los comandos terminan en `\n` (newline):

```bash
Cliente → Servidor:  "COMANDO param1 param2\n"
Servidor → Cliente:  "OK datos\n" o "ERROR mensaje\n"
```

### Parsing en TCPServer

```python
def _process_command(self, command: str, authenticated: bool, username: str) -> str:
    parts = command.split()
    cmd = parts[0].upper()
    
    if cmd == "LOGIN":
        user, password = parts[1], parts[2]
        if user in USUARIOS and USUARIOS[user] == password:
            return "OK LOGIN Bienvenido {user}"
        return "ERROR LOGIN: Credenciales inválidas"
    
    if cmd == "SET":
        if not authenticated:
            return "ERROR SET: Requiere autenticación"
        device_id = parts[1]
        subcommand = parts[2].upper()
        
        # Subcomandos de SET
        if subcommand == 'ON':
            if self.device_manager.set_device_state(device_id, 'ON'):
                return f"OK SET {device_id} ON"
        elif subcommand == 'OFF':
            if self.device_manager.set_device_state(device_id, 'OFF'):
                return f"OK SET {device_id} OFF"
        elif subcommand == 'BRIGHTNESS':
            value = int(parts[3])  # 0-100
            if self.device_manager.set_brightness(device_id, value):
                return f"OK SET {device_id} BRIGHTNESS {value}"
        elif subcommand == 'COLOR':
            color = parts[3]  # #RRGGBB
            if self.device_manager.set_color(device_id, color):
                return f"OK SET {device_id} COLOR {color}"
        elif subcommand == 'LEVEL':
            value = int(parts[3])  # 0-100 (cortinas)
            if self.device_manager.set_curtains(device_id, value):
                return f"OK SET {device_id} LEVEL {value}"
        elif subcommand == 'TEMP':
            value = int(parts[3])  # 16-30 (termostato)
            if self.device_manager.set_temperature(device_id, value):
                return f"OK SET {device_id} TEMP {value}"
        
        return f"ERROR SET: Subcomando o dispositivo no válido"
    # ...
```

### Subcomandos SET

| Subcomando | Sintaxis | Dispositivos | Descripción |
|------------|----------|--------------|-------------|
| `ON` | `SET <id> ON` | luz, enchufe | Encender dispositivo |
| `OFF` | `SET <id> OFF` | luz, enchufe | Apagar dispositivo |
| `BRIGHTNESS` | `SET <id> BRIGHTNESS <0-100>` | luz | Ajustar brillo |
| `COLOR` | `SET <id> COLOR <#RRGGBB>` | luz | Cambiar color |
| `LEVEL` | `SET <id> LEVEL <0-100>` | cortinas | Posición cortinas |
| `TEMP` | `SET <id> TEMP <16-30>` | termostato | Temperatura objetivo |

---

## API REST - Diseño

### Endpoints y Lógica

```python
@app.route('/api/status', methods=['GET'])
def get_status():
    """Thread-safe: device_manager usa Lock internamente"""
    devices = device_manager.get_all_devices()
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'devices': devices,
        'total': len(devices)
    })

@app.route('/api/control', methods=['POST'])
def control():
    """POST con JSON body - Encender/Apagar"""
    data = request.get_json()
    device_id = data['id']
    action = data['action'].upper()
    
    if device_manager.set_device_state(device_id, action):
        return jsonify({
            'success': True,
            'device_id': device_id,
            'new_state': action
        })
    return jsonify({'success': False, 'error': 'Dispositivo no encontrado'}), 404

@app.route('/api/brightness', methods=['POST'])
def set_brightness():
    """Ajustar brillo de luces (0-100)"""
    data = request.get_json()
    device_id = data['id']
    brightness = int(data['brightness'])
    device_manager.set_brightness(device_id, brightness)
    return jsonify({'success': True, 'brightness': brightness})

@app.route('/api/color', methods=['POST'])
def set_color():
    """Cambiar color de luces (#RRGGBB)"""
    data = request.get_json()
    device_id = data['id']
    color = data['color']
    device_manager.set_color(device_id, color)
    return jsonify({'success': True, 'color': color})

@app.route('/api/curtains', methods=['POST'])
def set_curtains():
    """Posición de cortinas (0-100%)"""
    data = request.get_json()
    device_id = data.get('id', 'cortinas')
    position = int(data['position'])
    device_manager.set_curtains(device_id, position)
    return jsonify({'success': True, 'position': position})

@app.route('/api/temperature', methods=['POST'])
def set_temperature():
    """Temperatura objetivo del termostato (16-30°C)"""
    data = request.get_json()
    device_id = data.get('id', 'termostato')
    temperature = int(data['temperature'])
    device_manager.set_temperature(device_id, temperature)
    return jsonify({'success': True, 'temperature': temperature})
```

### Tabla de Endpoints REST

| Endpoint | Método | Body | Descripción |
|----------|--------|------|-------------|
| `/api/status` | GET | - | Estado de todos los dispositivos |
| `/api/control` | POST | `{id, action}` | Encender/Apagar |
| `/api/brightness` | POST | `{id, brightness}` | Brillo 0-100 |
| `/api/color` | POST | `{id, color}` | Color #RRGGBB |
| `/api/curtains` | POST | `{id?, position}` | Cortinas 0-100% |
| `/api/temperature` | POST | `{id?, temperature}` | Temp 16-30°C |
| `/api/auto_off` | POST | `{id, segundos}` | Configurar auto-off |
| `/api/log` | GET | - | Últimos 100 eventos |

### CORS

Flask-CORS habilitado para permitir requests desde `file://` (HTML local):

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite todas las origins (solo desarrollo)
```

---

## Modelo de Datos

### Clase Device

```python
class Device:
    def __init__(self, device_id: str, device_type: str, estado: str = 'OFF'):
        self.id = device_id              # Identificador único
        self.type = device_type          # 'luz', 'enchufe', 'cortinas', 'termostato'
        
        # Estado y auto_off solo para dispositivos que se encienden/apagan
        if device_type in ['cortinas', 'termostato']:
            self.estado = 'N/A'          # Cortinas y termostato no tienen estado ON/OFF
            self.auto_off = 0            # No aplica auto-off
        else:
            self.estado = estado         # 'ON' o 'OFF'
            self.auto_off = 0            # Segundos (0 = desactivado)
        
        self.ultimo_cambio = datetime.now().isoformat()
        self.auto_off_timer = None       # threading.Timer o None (solo luces/enchufes)
        
        # Parámetros específicos por tipo
        self.brightness = 40 if device_type == 'luz' else 0       # Solo luces
        self.color = '#ffffff' if device_type == 'luz' else '#000000'  # Solo luces
        self.curtains = 50 if device_type == 'cortinas' else 0    # Solo cortinas
        self.temperature = 19 if device_type == 'termostato' else 0    # Solo termostato
        self.target_temperature = 21 if device_type == 'termostato' else 0
```

### Tipos de Dispositivos

| Tipo | Estado | Auto-Off | Parámetros Específicos |
|------|--------|----------|------------------------|
| `luz` | ON/OFF | Sí | brightness (0-100), color (#RRGGBB) |
| `enchufe` | ON/OFF | Sí | - |
| `cortinas` | N/A | No | curtains (0-100% posición) |
| `termostato` | N/A | No | temperature, target_temperature (16-30°C) |

### Estado Compartido (DeviceManager)

```python
class DeviceManager:
    def __init__(self):
        self.devices: Dict[str, Device] = {
            'luz_salon': Device('luz_salon', 'luz'),
            'enchufe_tv': Device('enchufe_tv', 'enchufe'),
            'enchufe_calefactor': Device('enchufe_calefactor', 'enchufe'),
            'cortinas': Device('cortinas', 'cortinas'),
            'termostato': Device('termostato', 'termostato')
        }
        self.log: List[str] = []         # Últimas 100 entradas
        self.lock = threading.Lock()     # Protección thread-safe
```

---

## Gestión de Timers

### Creación de Timer de Autoapagado

```python
def set_auto_off(self, device_id: str, segundos: int) -> bool:
    with self.lock:
        device = self.devices.get(device_id)
        
        # Cancelar timer anterior si existe
        if device.auto_off_timer:
            device.auto_off_timer.cancel()
        
        device.auto_off = segundos
        
        if segundos > 0:
            # Crear nuevo timer (daemon thread)
            device.auto_off_timer = threading.Timer(
                segundos, 
                self._auto_off_callback,  # Función a ejecutar
                args=[device_id]
            )
            device.auto_off_timer.daemon = True
            device.auto_off_timer.start()
```

### Callback del Timer

```python
def _auto_off_callback(self, device_id: str):
    """Ejecutado en thread separado cuando expira el timer"""
    with self.lock:  # Thread-safe
        device = self.devices.get(device_id)
        if device and device.estado == 'ON':
            device.estado = 'OFF'
            device.ultimo_cambio = datetime.now().isoformat()
            device.auto_off = 0
            device.auto_off_timer = None
            self._add_log(device_id, "Auto-apagado ejecutado")
```

**Importante:** El timer se cancela si:

- Se cambia el estado manualmente (SET OFF/ON)
- Se configura un nuevo autoapagado
- El dispositivo es controlado antes de que expire

---

## Logging de Eventos

### Formato de Entradas

```bash
[2025-11-19 14:30:00] luz_salon: Estado cambiado a ON
[2025-11-19 14:30:15] luz_salon: Auto-apagado programado en 30s
[2025-11-19 14:30:45] luz_salon: Auto-apagado ejecutado
```

### Implementación

```python
def _add_log(self, device_id: str, mensaje: str):
    """Thread-safe: debe llamarse dentro de with self.lock"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {device_id}: {mensaje}"
    self.log.append(log_entry)
    
    # Limitar a últimas 100 entradas
    if len(self.log) > 100:
        self.log = self.log[-100:]
    
    print(f"LOG: {log_entry}")  # Debug en consola del servidor
```

---

## Gestión de Conexiones TCP

### Aceptar Múltiples Clientes

```python
class TCPServer:
    def _run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # Cola de hasta 5 conexiones
        
        while self.running:
            client_socket, address = self.server_socket.accept()
            
            # Nuevo thread por cada cliente
            client_thread = threading.Thread(
                target=self._handle_client,
                args=(client_socket, address),
                daemon=True  # Se cierra cuando main thread termina
            )
            client_thread.start()
```

### Ciclo de Vida de Conexión

```python
def _handle_client(self, client_socket, address):
    authenticated = False
    username = None
    
    try:
        client_socket.send(b"SERVIDOR DOMOTICO v1.0\n...")
        
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break  # Cliente desconectado
            
            response = self._process_command(data, authenticated, username)
            
            if response.startswith("OK LOGIN"):
                authenticated = True
                username = data.split()[1]
            
            client_socket.send((response + "\n").encode('utf-8'))
            
            if data.upper() == "EXIT":
                break
    finally:
        client_socket.close()
```

---

## Gemelo Digital Web - Arquitectura Frontend

### Actualización Automática

```javascript
const UPDATE_INTERVAL = 5000; // 5 segundos

function startAutoUpdate() {
    loadDevices();  // Carga inicial
    
    updateTimer = setInterval(() => {
        loadDevices();  // Recargar cada 5s
    }, UPDATE_INTERVAL);
}

async function loadDevices() {
    const response = await fetch(`${API_BASE_URL}/status`);
    const data = await response.json();
    
    if (data.success) {
        renderDevices(data.devices);  // Actualizar DOM
        updateLastUpdateTime();
    }
}
```

### Control Bidireccional

```javascript
async function controlDevice(deviceId, action) {
    const response = await fetch(`${API_BASE_URL}/control`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: deviceId, action: action })
    });
    
    const data = await response.json();
    
    if (data.success) {
        showNotification(`Dispositivo ${action}`, 'success');
        loadDevices();  // Refrescar UI
    }
}
```

---

## Puertos y Servicios

| Puerto | Protocolo | Servicio | Uso |
|--------|-----------|----------|-----|
| 5000 | TCP | TCPServer | Comandos de control (cliente CLI) |
| 5001 | UDP | UDPBroadcaster | Telemetría broadcast (monitorización) |
| 8080 | HTTP (TCP) | Flask API | REST API (gemelo digital web) |

---

## Seguridad - Limitaciones Conocidas

⚠️ **Sistema educativo - NO usar en producción sin mejoras:**

1. **Autenticación básica**
   - Contraseñas en texto plano en código
   - Sin hashing (bcrypt/argon2)
   - Sin tokens de sesión

2. **Sin cifrado**
   - TCP sin TLS/SSL
   - HTTP sin HTTPS
   - Passwords viajan en claro

3. **Sin persistencia**
   - Estado volátil (se pierde al reiniciar)
   - No hay base de datos

4. **CORS permisivo**
   - Permite todas las origins (desarrollo)

**Para producción se necesitaría:**

- JWT para autenticación
- HTTPS/TLS para cifrado
- Base de datos (SQLite/PostgreSQL)
- Hashing de contraseñas
- Rate limiting
- Input validation estricta
- Logging de auditoría

---

## Patrones de Diseño Utilizados

1. **Singleton** - DeviceManager (compartido entre componentes)
2. **Factory** - `create_api()` para crear app Flask
3. **Observer** - UDP broadcast (broadcasting pattern)
4. **Thread Pool** - Múltiples clientes TCP concurrentes
5. **MVC** - Separación Model (Device) / View (Web/CLI) / Controller (Managers)

---

## Escalabilidad

### Limitaciones Actuales

- Dispositivos hardcoded (5 fijos: 1 luz, 2 enchufes, cortinas, termostato)
- Sin base de datos
- Estado en memoria (no distribuido)
- Single server (no cluster)

### Mejoras Posibles

- Configuración dinámica de dispositivos (JSON/YAML)
- Persistencia con SQLAlchemy
- Redis para caché distribuida
- Load balancer para múltiples instancias
- Message queue (RabbitMQ/Kafka) para escalado horizontal

---

## Testing

Ver `scripts/test_sistema.py` para suite completa de tests que valida:

- Conexiones TCP
- Todos los comandos del protocolo
- Autenticación
- API REST endpoints
- Concurrencia
- Funcionalidad de autoapagado

---

## Fin de la documentación técnica
