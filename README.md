# 🏠 Sistema Domótico IoT - Control Inteligente de Dispositivos

Sistema completo de domótica basado en arquitectura Cliente-Servidor con capacidades IoT, gemelo digital web y telemetría en tiempo real.

## 📋 Características Principales

- **Arquitectura Cliente-Servidor** con triple protocolo (TCP + UDP + REST)
- **Control de 4 dispositivos** virtuales (2 luces + 2 enchufes)
- **Autoapagado programable** con threading.Timer
- **Gemelo Digital Web** con interfaz moderna y actualización automática
- **Telemetría en tiempo real** vía UDP broadcast
- **Concurrencia real** con threading y locks (thread-safe)
- **Cliente CLI interactivo** para terminal
- **API REST JSON** para integración con aplicaciones

---

## 🚀 Inicio Rápido (3 Pasos)

### 1. Instalar (solo la primera vez)

```powershell
.\scripts\install.ps1
```

Esto creará un entorno virtual (`venv/`) e instalará todas las dependencias.

### 2. Iniciar el servidor

```powershell
.\scripts\start.ps1
```

O manualmente:
```powershell
.\venv\Scripts\Activate.ps1
python server\server_domotico.py
```

### 3. Usar el sistema

**Opción A: Cliente de Consola (Terminal)**
```powershell
.\venv\Scripts\Activate.ps1
python client\client_console.py
```
- Login: `admin` / `admin123` o `user` / `pass123`
- Menú con 8 opciones para controlar dispositivos

**Opción B: Gemelo Digital Web** ⭐ Recomendado
- Abrir `web\web_dashboard.html` en el navegador
- Interfaz visual moderna con actualización automática

**Opción C: Monitor de Telemetría UDP**
```powershell
.\venv\Scripts\Activate.ps1
python client\udp_listener.py
```
- Muestra el estado broadcast cada 2 segundos

---

## 📁 Estructura del Proyecto

```
Miniproyecto/
├── server/                    # Servidor central
│   └── server_domotico.py     # Lógica principal (TCP/UDP/REST)
│
├── client/                    # Aplicaciones cliente
│   ├── client_console.py      # Cliente CLI interactivo
│   └── udp_listener.py        # Monitor de telemetría
│
├── web/                       # Gemelo digital web
│   └── web_dashboard.html     # Interfaz HTML+JS+CSS
│
├── scripts/                   # Automatización
│   ├── install.ps1            # Instalador con venv
│   ├── start.ps1              # Inicio rápido
│   └── test_sistema.py        # Suite de pruebas
│
├── docs/                      # Documentación técnica
│   └── ARQUITECTURA.md        # Diagramas y detalles
│
├── venv/                      # Entorno virtual (creado por install.ps1)
├── requirements.txt           # Dependencias Python
├── .gitignore                 # Configuración Git
└── README.md                  # Este archivo
```

---

## 🔧 Componentes del Sistema

### Servidor (`server/server_domotico.py`)

Servidor central multi-hilo que gestiona todo el sistema:

- **TCP Socket (Puerto 5000)** - Comandos de control directo
- **UDP Broadcast (Puerto 5001)** - Telemetría cada 2 segundos
- **API REST (Puerto 8080)** - Endpoints JSON para gemelo digital

**Clases principales:**
- `Device` - Modelo de dispositivo
- `DeviceManager` - Lógica de negocio (thread-safe con locks)
- `TCPServer` - Servidor de comandos TCP
- `UDPBroadcaster` - Emisor de telemetría
- `DomoticServer` - Orquestador principal

### Cliente Terminal (`client/client_console.py`)

Cliente interactivo con menú CLI:
- Autenticación de usuarios
- Control completo de dispositivos
- Consulta de estado y logs
- Configuración de autoapagado

### Gemelo Digital (`web/web_dashboard.html`)

Interfaz web moderna:
- Visualización en tiempo real de dispositivos
- Control ON/OFF con botones
- Configuración de autoapagado
- Historial de eventos
- Actualización automática cada 5 segundos

---

## 📡 Protocolos de Comunicación

### TCP - Comandos de Control (Puerto 5000)

**Comandos disponibles:**

| Comando | Descripción | Requiere Auth |
|---------|-------------|---------------|
| `LOGIN <user> <pass>` | Autenticación | No |
| `LIST` | Listar dispositivos | No |
| `STATUS <id>` | Estado de dispositivo | No |
| `SET <id> <ON\|OFF>` | Encender/Apagar | **Sí** |
| `AUTO_OFF <id> <seg>` | Programar apagado | **Sí** |
| `LOG` | Ver historial | No |
| `EXIT` | Cerrar conexión | No |

**Ejemplo de uso:**
```
> LOGIN admin admin123
< OK LOGIN Bienvenido admin

> LIST
< OK 4 luz_salon,OFF,0;luz_dormitorio,OFF,0;enchufe_tv,OFF,0;enchufe_calefactor,OFF,0

> SET luz_salon ON
< OK SET luz_salon ON

> AUTO_OFF luz_salon 30
< OK AUTO_OFF luz_salon 30s
```

### UDP - Telemetría (Puerto 5001)

Broadcast automático cada 2 segundos en formato JSON:

```json
{
  "timestamp": "2025-11-19T14:30:00.123456",
  "devices": [
    {
      "id": "luz_salon",
      "type": "luz",
      "estado": "ON",
      "auto_off": 0,
      "ultimo_cambio": "2025-11-19T14:25:30.123456"
    }
  ]
}
```

### REST API - Gemelo Digital (Puerto 8080)

**Endpoints disponibles:**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/status` | Estado de todos los dispositivos |
| GET | `/api/device/<id>` | Estado de un dispositivo |
| POST | `/api/control` | Controlar ON/OFF |
| POST | `/api/auto_off` | Configurar autoapagado |
| GET | `/api/log?limit=20` | Historial de eventos |

**Ejemplo POST /api/control:**
```json
{
  "id": "luz_salon",
  "action": "ON"
}
```

**Respuesta:**
```json
{
  "success": true,
  "device_id": "luz_salon",
  "new_state": "ON"
}
```

---

## 🎯 Dispositivos Disponibles

| ID | Tipo | Icono | Descripción |
|----|------|-------|-------------|
| `luz_salon` | luz | 💡 | Luz principal del salón |
| `luz_dormitorio` | luz | 💡 | Luz del dormitorio |
| `enchufe_tv` | enchufe | 📺 | Smart plug para TV |
| `enchufe_calefactor` | enchufe | 🔥 | Smart plug para calefacción |

---

## 🔐 Usuarios de Prueba

| Usuario | Contraseña | Permisos |
|---------|------------|----------|
| `admin` | `admin123` | Completos |
| `user` | `pass123` | Completos |

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Encender luz desde CLI
```powershell
python client\client_console.py
# 1. Opción 1: Login (admin/admin123)
# 2. Opción 4: Encender/Apagar
# 3. ID: luz_salon
# 4. Estado: ON
```

### Ejemplo 2: Autoapagado desde Web
1. Abrir `web\web_dashboard.html`
2. Click en "Encender" de `luz_dormitorio`
3. En "Auto-apagado", escribir `30`
4. Click en "Aplicar"
5. Esperar 30 segundos → se apaga automáticamente

### Ejemplo 3: Monitorizar telemetría
```powershell
python client\udp_listener.py
# Verás actualizaciones cada 2 segundos con el estado completo
```

---

## 🧪 Testing

Ejecutar suite de pruebas automatizadas (20+ tests):

```powershell
.\venv\Scripts\Activate.ps1
python scripts\test_sistema.py
```

**Tests incluidos:**
- ✅ Conexión TCP
- ✅ Protocolo de comandos (7 comandos)
- ✅ Autenticación y seguridad
- ✅ API REST (5 endpoints)
- ✅ Funcionalidad de autoapagado
- ✅ Operaciones concurrentes

---

## 🛠️ Solución de Problemas

### ❌ "No se pudo conectar al servidor"
**Causa:** El servidor no está en ejecución  
**Solución:** Ejecuta `.\scripts\start.ps1` primero

### ❌ "ModuleNotFoundError"
**Causa:** Dependencias no instaladas o venv no activado  
**Solución:**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### ❌ "Address already in use"
**Causa:** Ya hay un servidor corriendo en el puerto  
**Solución:**
```powershell
# Buscar proceso
netstat -ano | findstr :5000
# Terminar proceso
taskkill /PID <PID> /F
```

### ❌ Dashboard web no carga dispositivos
**Causa:** Servidor no está corriendo o problema CORS  
**Solución:**
1. Verifica que el servidor esté activo
2. Abre la consola del navegador (F12) y revisa errores
3. Asegúrate de usar `http://localhost:8080` (no HTTPS)

---

## 🔒 Seguridad y Concurrencia

### Thread-Safety
- `threading.Lock` protege acceso a datos compartidos en `DeviceManager`
- Sin race conditions
- Múltiples clientes pueden conectarse simultáneamente

### Autenticación
- Sistema simple con usuarios hardcoded (solo para desarrollo/educación)
- Comandos de lectura (`LIST`, `STATUS`, `LOG`) son públicos
- Comandos de escritura (`SET`, `AUTO_OFF`) requieren autenticación

⚠️ **Advertencia:** Este sistema es para desarrollo/educación. Para producción se necesitaría:
- HTTPS/TLS para cifrado
- Base de datos para persistencia
- Sistema de autenticación robusto (JWT, OAuth)
- Hashing de contraseñas (bcrypt)

---

## 📚 Documentación Adicional

Para detalles técnicos avanzados, consulta:
- `docs/ARQUITECTURA.md` - Diagramas de flujos, threading, protocolos

---

## 🎓 Conceptos Técnicos Demostrados

- ✅ Sockets TCP y UDP
- ✅ API RESTful con Flask
- ✅ Threading y concurrencia
- ✅ Sincronización con locks
- ✅ Gemelo Digital (Digital Twin)
- ✅ Telemetría IoT
- ✅ Protocolo de texto personalizado
- ✅ SPA con JavaScript (Fetch API)
- ✅ Testing automatizado

---

## 🌟 Tecnologías Utilizadas

- **Python 3.8+** - Lenguaje principal
- **Flask 3.0** - Framework web para API REST
- **flask-cors** - CORS para desarrollo web
- **socket** - TCP/UDP de bajo nivel
- **threading** - Concurrencia y paralelismo
- **HTML5 + CSS3 + JavaScript** - Frontend web

---

## 📦 Dependencias

Ver `requirements.txt`:
- Flask==3.0.0
- flask-cors==4.0.0
- Werkzeug==3.0.1
- requests==2.31.0 (solo para tests)

---

## 🎯 Comandos Útiles

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Desactivar entorno virtual
deactivate

# Instalar dependencias manualmente
pip install -r requirements.txt

# Ejecutar servidor
python server\server_domotico.py

# Ejecutar cliente CLI
python client\client_console.py

# Ejecutar tests
python scripts\test_sistema.py
```

---

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

---

## 👨‍💻 Autor

Sistema Domótico IoT - Proyecto Educativo  
Arquitectura Cliente-Servidor  
Noviembre 2025

---

**¿Problemas o preguntas?** Revisa los logs del servidor en consola o consulta `docs/ARQUITECTURA.md` para detalles técnicos.
