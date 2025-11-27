# 🏠 Sistema Domótico IoT - Control Inteligente de Dispositivos

Sistema completo de domótica basado en arquitectura Cliente-Servidor con capacidades IoT, gemelo digital web, simulador 3D y asistente de voz con IA.

---

## 📋 Características Principales

### 🔌 Control de Dispositivos

- **5 dispositivos inteligentes** con control completo:
  - 💡 **Luz del salón** - ON/OFF, brillo (0-100%), color RGB
  - 📺 **Enchufe TV** - ON/OFF con auto-apagado programable
  - 🔥 **Enchufe Calefactor** - ON/OFF con auto-apagado programable
  - 🪟 **Cortinas motorizadas** - Posición 0-100%
  - 🌡️ **Termostato** - Temperatura objetivo 16-30°C

### 🌐 Comunicaciones

- **Triple protocolo** de comunicación:
  - **TCP (Puerto 5000)** - Comandos de control en tiempo real
  - **UDP (Puerto 5001)** - Telemetría broadcast cada 2 segundos
  - **REST API (Puerto 8080)** - Integración web y aplicaciones

### 🤖 Asistente IA - Jarvis

- **Chatbot integrado** con Google Gemini
- **Control por voz** con reconocimiento de voz del navegador
- Comandos en **lenguaje natural**: "Enciende la luz", "Activa modo cine", etc.
- Ejecución automática de acciones múltiples

### 🎮 Interfaces de Usuario

- **Dashboard Web** - Panel de control moderno con actualización automática
- **Simulador 3D** - Visualización interactiva con React + Three.js
- **Cliente CLI** - Terminal interactivo con modo guiado
- **Monitor UDP** - Telemetría en tiempo real

### ⚙️ Características Técnicas

- **Concurrencia real** con threading y locks (thread-safe)
- **Auto-apagado programable** con temporizadores
- **Sincronización bidireccional** entre todas las interfaces
- **Historial de eventos** con últimas 100 acciones

---

## 🚀 Inicio Rápido

### 1️⃣ Instalación (solo primera vez)

```powershell
.\scripts\install.ps1
```

Esto instalará:

- Entorno virtual Python con dependencias
- Dependencias de Node.js para el simulador 3D

### 2️⃣ Configurar API Key de Gemini (opcional, para chatbot IA)

```powershell
$env:GEMINI_API_KEY = "tu-api-key-de-google-ai"
```

> Obtén tu API Key gratis en: https://aistudio.google.com/apikey

### 3️⃣ Iniciar el Sistema

```powershell
.\scripts\start.ps1
```

Esto inicia automáticamente:

- Servidor domótico (puertos 5000, 5001, 8080)
- Simulador 3D (puerto 3000)

### 4️⃣ Acceder al Sistema

| Interfaz | URL/Comando |
|----------|-------------|
| 🌐 **Dashboard Web** | Abrir `web\web_dashboard.html` en navegador |
| 🎮 **Simulador 3D** | http://localhost:3000 (o pestaña en dashboard) |
| 💻 **Cliente CLI** | `python client\client_console.py` |
| 📡 **Monitor UDP** | `python client\udp_listener.py` |

---

## 📁 Estructura del Proyecto

```
Miniproyecto/
├── server/
│   └── server_domotico.py     # Servidor central (TCP/UDP/REST/Gemini)
│
├── client/
│   ├── client_console.py      # Cliente CLI interactivo
│   └── udp_listener.py        # Monitor de telemetría UDP
│
├── web/
│   ├── web_dashboard.html     # Dashboard web con chatbot
│   └── web_server.py          # Servidor HTTP para dashboard
│
├── home_simulator/            # Simulador 3D
│   ├── App.tsx                # Componente principal React
│   ├── components/            # Escena 3D y controles
│   ├── services/              # Conexión con API
│   └── package.json           # Dependencias Node.js
│
├── scripts/
│   ├── install.ps1            # Instalador automático
│   ├── start.ps1              # Inicio rápido del sistema
│   └── test_sistema.py        # Suite de pruebas
│
├── docs/
│   └── ARQUITECTURA.md        # Documentación técnica detallada
│
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

---

## 🔧 Componentes del Sistema

### 🖥️ Servidor Central (`server/server_domotico.py`)

Núcleo del sistema que gestiona todas las comunicaciones:

| Componente | Puerto | Función |
|------------|--------|---------|
| **TCPServer** | 5000 | Comandos de control directo |
| **UDPBroadcaster** | 5001 | Telemetría broadcast (cada 2s) |
| **Flask API** | 8080 | REST API + Chatbot Gemini |
| **DeviceManager** | - | Lógica de negocio (thread-safe) |

### 💬 Chatbot Jarvis

Asistente de IA integrado en el dashboard web:

- **Motor**: Google Gemini 1.5 Flash
- **Entrada**: Texto o voz (micrófono)
- **Capacidades**:
  - Control de todos los dispositivos
  - Consulta de estado actual
  - Comandos complejos ("modo cine", "hace frío")
  - Respuestas en lenguaje natural

**Ejemplos de comandos de voz:**

- "Enciende la luz del salón"
- "Pon el brillo al 50%"
- "Cambia el color a azul"
- "Abre las cortinas"
- "Sube la temperatura a 23 grados"
- "Activa el modo cine" (baja luces, cierra cortinas, enciende TV)

### 🎮 Simulador 3D (`home_simulator/`)

Visualización 3D interactiva de la habitación:

- **Tecnologías**: React 19 + Three.js + TypeScript
- **Sincronización**: Polling cada 2 segundos
- **Controles**: Sliders, botones, color picker
- **Indicador**: Estado de conexión en tiempo real

### 📊 Dashboard Web (`web/web_dashboard.html`)

Panel de control completo:

- **Pestañas**: Panel de Control | Simulador 3D
- **Controles visuales** para todos los dispositivos
- **Chatbot flotante** con micrófono
- **Historial de eventos** en tiempo real
- **Actualización automática** cada 5 segundos

---

## 📡 Protocolo TCP (Puerto 5000)

### Comandos Disponibles

| Comando | Sintaxis | Auth | Descripción |
|---------|----------|------|-------------|
| `LOGIN` | `LOGIN &lt;user&gt; &lt;pass&gt;` | No | Autenticación |
| `LIST` | `LIST` | No | Listar dispositivos |
| `STATUS` | `STATUS &lt;id&gt;` | No | Estado de un dispositivo |
| `SET` | `SET &lt;id&gt; &lt;acción&gt; [valor]` | Sí | Controlar dispositivo |
| `AUTO_OFF` | `AUTO_OFF &lt;id&gt; &lt;segundos&gt;` | Sí | Programar auto-apagado |
| `LOG` | `LOG` | No | Ver historial |
| `EXIT` | `EXIT` | No | Cerrar conexión |

### Subcomandos SET

| Subcomando | Sintaxis | Dispositivos | Ejemplo |
|------------|----------|--------------|---------|
| `ON` | `SET &lt;id&gt; ON` | luz, enchufes | `SET luz_salon ON` |
| `OFF` | `SET &lt;id&gt; OFF` | luz, enchufes | `SET enchufe_tv OFF` |
| `BRIGHTNESS` | `SET &lt;id&gt; BRIGHTNESS &lt;0-100&gt;` | luz | `SET luz_salon BRIGHTNESS 75` |
| `COLOR` | `SET &lt;id&gt; COLOR &lt;#RRGGBB&gt;` | luz | `SET luz_salon COLOR #ff6600` |
| `LEVEL` | `SET cortinas LEVEL &lt;0-100&gt;` | cortinas | `SET cortinas LEVEL 80` |
| `TEMP` | `SET termostato TEMP &lt;16-30&gt;` | termostato | `SET termostato TEMP 22` |

### Ejemplo de Sesión TCP

```
> LOGIN admin admin123
< OK LOGIN Bienvenido admin

> LIST
< OK 5 luz_salon,OFF,0,40,#ffffff,0,0,0;...

> SET luz_salon ON
< OK SET luz_salon ON

> SET luz_salon BRIGHTNESS 75
< OK SET luz_salon BRIGHTNESS 75

> SET cortinas LEVEL 50
< OK SET cortinas LEVEL 50

> AUTO_OFF luz_salon 60
< OK AUTO_OFF luz_salon 60

> EXIT
< OK EXIT Hasta luego!
```

---

## 🌐 API REST (Puerto 8080)

### Endpoints Disponibles

| Método | Endpoint | Body | Descripción |
|--------|----------|------|-------------|
| GET | `/api/status` | - | Estado de todos los dispositivos |
| GET | `/api/device/&lt;id&gt;` | - | Estado de un dispositivo |
| POST | `/api/control` | `{id, action}` | Encender/Apagar |
| POST | `/api/brightness` | `{id, brightness}` | Ajustar brillo (0-100) |
| POST | `/api/color` | `{id, color}` | Cambiar color (#RRGGBB) |
| POST | `/api/curtains` | `{position}` | Posición cortinas (0-100%) |
| POST | `/api/temperature` | `{temperature}` | Temperatura (16-30°C) |
| POST | `/api/auto_off` | `{id, seconds}` | Configurar auto-apagado |
| POST | `/api/chat` | `{message}` | Chatbot IA Gemini |
| GET | `/api/log` | - | Historial de eventos |

### Ejemplos de Uso con cURL

**Encender luz:**

```bash
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"id": "luz_salon", "action": "ON"}'
```

**Ajustar brillo:**

```bash
curl -X POST http://localhost:8080/api/brightness \
  -H "Content-Type: application/json" \
  -d '{"id": "luz_salon", "brightness": 75}'
```

**Chatbot:**

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Enciende la luz y pon el brillo al 50%"}'
```

---

## 🎯 Dispositivos del Sistema

| ID | Tipo | Descripción | Parámetros | Estado |
|----|------|-------------|------------|--------|
| `luz_salon` | luz | Luz inteligente | brillo, color | ON/OFF |
| `enchufe_tv` | enchufe | Smart plug TV | auto_off | ON/OFF |
| `enchufe_calefactor` | enchufe | Smart plug calefactor | auto_off | ON/OFF |
| `cortinas` | cortinas | Cortinas motorizadas | posición (0-100%) | N/A |
| `termostato` | termostato | Control temperatura | temp actual, objetivo | N/A |

> **Nota:** Cortinas y termostato no tienen estado ON/OFF ni auto-apagado.

---

## 🔐 Usuarios de Prueba

| Usuario | Contraseña | Permisos |
|---------|------------|----------|
| `admin` | `admin123` | Completos |
| `user` | `pass123` | Completos |

---

## 💡 Casos de Uso

### Caso 1: Control por Voz

1. Abre el dashboard web
2. Haz clic en el botón 🤖 (chatbot)
3. Haz clic en el botón 🎤 (micrófono)
4. Di: "Activa el modo cine"
5. Jarvis bajará las luces, cerrará cortinas y encenderá la TV

### Caso 2: Programar Auto-apagado

1. Desde el dashboard, enciende `luz_salon`
2. En "Auto-apagado", escribe `300` (5 minutos)
3. Haz clic en "Aplicar"
4. La luz se apagará automáticamente después de 5 minutos

### Caso 3: Monitorizar Telemetría

```powershell
python client\udp_listener.py
```

Verás una tabla actualizada cada 2 segundos con el estado de todos los dispositivos.

---

## 🧪 Testing

Ejecutar suite completa de pruebas:

```powershell
.\venv\Scripts\Activate.ps1
python scripts\test_sistema.py
```

**Tests incluidos:**

- ✅ Conexión TCP
- ✅ Todos los comandos del protocolo
- ✅ Autenticación y seguridad
- ✅ API REST (todos los endpoints)
- ✅ Funcionalidad de auto-apagado
- ✅ Operaciones concurrentes

---

## 🛠️ Solución de Problemas

### ❌ "No se pudo conectar al servidor"

**Solución:** Ejecuta `.\scripts\start.ps1` primero

### ❌ "Chatbot no responde"

**Causa:** API Key de Gemini no configurada

**Solución:**

```powershell
$env:GEMINI_API_KEY = "tu-api-key"
# Reiniciar servidor
```

### ❌ "ModuleNotFoundError"

**Solución:**

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### ❌ "Address already in use"

**Solución:**

```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### ❌ "Micrófono no funciona"

**Causa:** Navegador sin permisos o no compatible

**Solución:** Usa Chrome/Edge y permite acceso al micrófono

---

## 📦 Dependencias

### Python (`requirements.txt`)

```
Flask==3.0.0
flask-cors==4.0.0
Werkzeug==3.0.1
requests==2.31.0
google-generativeai==0.8.3
```

### Node.js (`home_simulator/package.json`)

- React 19.2
- Three.js 0.181
- Vite 6.2
- TypeScript 5.7

---

## 🎓 Conceptos Técnicos Demostrados

- ✅ Sockets TCP y UDP
- ✅ API RESTful con Flask
- ✅ Threading y concurrencia
- ✅ Sincronización con locks
- ✅ Gemelo Digital (Digital Twin)
- ✅ Telemetría IoT
- ✅ Integración con IA (Google Gemini)
- ✅ Web Speech API (reconocimiento de voz)
- ✅ Renderizado 3D con Three.js
- ✅ Protocolo de texto personalizado

---

## 📚 Documentación Adicional

Para detalles técnicos avanzados, consulta:

- [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) - Diagramas, flujos, threading

---

## 👨‍💻 Autor

Sistema Domótico IoT - Proyecto Educativo  
Comunicaciones Industriales - ICAI  
Noviembre 2025

---

**¿Problemas?** Revisa los logs del servidor en consola o consulta `docs/ARQUITECTURA.md`.
