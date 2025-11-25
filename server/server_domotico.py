#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Domótico - Servidor Central
====================================
Arquitectura: Cliente-Servidor con doble protocolo TCP/UDP + API REST
Autor: Sistema Domótico IoT
Fecha: Noviembre 2025

Características:
- Gestión de dispositivos (luces y enchufes)
- Autoapagado programable
- Concurrencia mediante threading
- TCP para comandos (puerto 5000)
- UDP para telemetría broadcast (puerto 5001)
- API REST JSON para gemelo digital (puerto 8080)
"""

import socket
import threading
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# ==================== CONFIGURACIÓN ====================
TCP_HOST = "0.0.0.0"
TCP_PORT = 5000
UDP_PORT = 5001
API_PORT = 8080
BROADCAST_INTERVAL = 2  # segundos

# Usuarios autorizados (simulación simple)
USUARIOS = {"admin": "admin123", "user": "pass123"}


# ==================== MODELO DE DISPOSITIVO ====================
class Device:
    """Representa un dispositivo domótico (luz o enchufe)"""

    def __init__(self, device_id: str, device_type: str, estado: str = "OFF"):
        self.id = device_id
        self.type = device_type  # 'luz', 'enchufe', 'cortinas', 'termostato'

        # Estado y auto_off solo para dispositivos que se encienden/apagan
        if device_type in ["cortinas", "termostato"]:
            self.estado = "N/A"  # Cortinas y termostato no tienen estado ON/OFF
            self.auto_off = 0  # No aplica auto-off
        else:
            self.estado = estado  # 'ON' o 'OFF'
            self.auto_off = 0  # segundos para apagado automático (0 = desactivado)

        self.ultimo_cambio = datetime.now().isoformat()
        self.auto_off_timer = None  # Temporizador activo (solo para luces/enchufes)

        # Parámetros específicos por tipo de dispositivo
        self.brightness = 40 if device_type == "luz" else 0  # Intensidad de luz (0-100)
        self.color = (
            "#ffffff" if device_type == "luz" else "#000000"
        )  # Color de luz (hex)
        self.curtains = (
            50 if device_type == "cortinas" else 0
        )  # Posición de cortinas (0-100)
        self.temperature = (
            19 if device_type == "termostato" else 0
        )  # Temperatura actual
        self.target_temperature = (
            21 if device_type == "termostato" else 0
        )  # Temperatura objetivo

    def to_dict(self) -> dict:
        """Serializa el dispositivo a diccionario"""
        return {
            "id": self.id,
            "type": self.type,
            "estado": self.estado,
            "auto_off": self.auto_off,
            "ultimo_cambio": self.ultimo_cambio,
            "brightness": self.brightness,
            "color": self.color,
            "curtains": self.curtains,
            "temperature": self.temperature,
            "target_temperature": self.target_temperature,
        }

    def to_protocol_string(self) -> str:
        """Formato para protocolo de texto: id,estado,auto_off,brightness,color,curtains,temp,target_temp"""
        return f"{self.id},{self.estado},{self.auto_off},{self.brightness},{self.color},{self.curtains},{self.temperature},{self.target_temperature}"


# ==================== GESTOR DE DISPOSITIVOS ====================
class DeviceManager:
    """
    Núcleo de lógica de negocio del sistema domótico.
    Maneja el estado de todos los dispositivos, autoapagado y registro de eventos.
    Thread-safe mediante Lock.
    """

    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.log: List[str] = []
        self.lock = threading.Lock()  # Protección contra condiciones de carrera
        self._initialize_devices()

    def _initialize_devices(self):
        """Inicializa los dispositivos predefinidos"""
        dispositivos_iniciales = [
            ("luz_salon", "luz"),
            ("enchufe_tv", "enchufe"),
            ("enchufe_calefactor", "enchufe"),
            ("cortinas", "cortinas"),
            ("termostato", "termostato"),
        ]

        with self.lock:
            for dev_id, dev_type in dispositivos_iniciales:
                self.devices[dev_id] = Device(dev_id, dev_type)
            self._add_log("SISTEMA", "Dispositivos inicializados")

    def _add_log(self, device_id: str, mensaje: str):
        """Añade entrada al historial (thread-safe)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {device_id}: {mensaje}"
        self.log.append(log_entry)

        # Limitar a las últimas 100 entradas
        if len(self.log) > 100:
            self.log = self.log[-100:]

        print(f"LOG: {log_entry}")  # Debug en consola

    def get_all_devices(self) -> List[dict]:
        """Obtiene todos los dispositivos (thread-safe)"""
        with self.lock:
            return [dev.to_dict() for dev in self.devices.values()]

    def get_device(self, device_id: str) -> Optional[dict]:
        """Obtiene un dispositivo específico"""
        with self.lock:
            device = self.devices.get(device_id)
            return device.to_dict() if device else None

    def set_device_state(self, device_id: str, nuevo_estado: str) -> bool:
        """
        Cambia el estado de un dispositivo (ON/OFF)
        Retorna True si tiene éxito, False si el dispositivo no existe
        """
        with self.lock:
            device = self.devices.get(device_id)
            if not device:
                return False

            # Cancelar temporizador previo si existe
            if device.auto_off_timer:
                device.auto_off_timer.cancel()
                device.auto_off_timer = None
                device.auto_off = 0

            device.estado = nuevo_estado
            device.ultimo_cambio = datetime.now().isoformat()
            self._add_log(device_id, f"Estado cambiado a {nuevo_estado}")
            return True

    def set_auto_off(self, device_id: str, segundos: int) -> bool:
        """
        Programa el apagado automático de un dispositivo
        """
        with self.lock:
            device = self.devices.get(device_id)
            if not device:
                return False

            # Cancelar temporizador anterior si existe
            if device.auto_off_timer:
                device.auto_off_timer.cancel()

            device.auto_off = segundos

            if segundos > 0:
                # Crear nuevo temporizador
                device.auto_off_timer = threading.Timer(
                    segundos, self._auto_off_callback, args=[device_id]
                )
                device.auto_off_timer.daemon = True
                device.auto_off_timer.start()
                self._add_log(device_id, f"Auto-apagado programado en {segundos}s")
            else:
                device.auto_off_timer = None
                self._add_log(device_id, "Auto-apagado cancelado")

            return True

    def _auto_off_callback(self, device_id: str):
        """
        Callback ejecutado cuando el temporizador de autoapagado expira
        """
        with self.lock:
            device = self.devices.get(device_id)
            if device and device.estado == "ON":
                device.estado = "OFF"
                device.ultimo_cambio = datetime.now().isoformat()
                device.auto_off = 0
                device.auto_off_timer = None
                self._add_log(device_id, "Auto-apagado ejecutado")

    def set_brightness(self, device_id: str, brightness: int) -> bool:
        """Establece el brillo de una luz (0-100)"""
        with self.lock:
            device = self.devices.get(device_id)
            if not device or device.type != "luz":
                return False
            device.brightness = max(0, min(100, brightness))
            device.ultimo_cambio = datetime.now().isoformat()
            self._add_log(device_id, f"Brillo cambiado a {device.brightness}%")
            return True

    def set_color(self, device_id: str, color: str) -> bool:
        """Establece el color de una luz (formato hex #RRGGBB)"""
        with self.lock:
            device = self.devices.get(device_id)
            if not device or device.type != "luz":
                return False
            device.color = color
            device.ultimo_cambio = datetime.now().isoformat()
            self._add_log(device_id, f"Color cambiado a {color}")
            return True

    def set_curtains(self, curtains: int) -> bool:
        """Establece la posición de las cortinas (0-100)"""
        with self.lock:
            device = self.devices.get("cortinas")
            if not device:
                return False
            curtains = max(0, min(100, curtains))
            device.curtains = curtains
            device.ultimo_cambio = datetime.now().isoformat()
            self._add_log("cortinas", f"Posición ajustada a {curtains}%")
            return True

    def set_temperature(self, target_temp: float) -> bool:
        """Establece la temperatura objetivo"""
        with self.lock:
            device = self.devices.get("termostato")
            if not device:
                return False
            target_temp = max(16, min(30, target_temp))
            device.target_temperature = target_temp
            device.ultimo_cambio = datetime.now().isoformat()
            self._add_log("termostato", f"Temperatura objetivo: {target_temp}°C")
            return True

    def get_log(self, limit: int = 20) -> List[str]:
        """Obtiene el historial de eventos"""
        with self.lock:
            return self.log[-limit:]

    def get_protocol_list(self) -> str:
        """
        Retorna lista de dispositivos en formato protocolo texto:
        OK <cantidad> id1,estado1,auto_off1;id2,estado2,auto_off2;...
        """
        with self.lock:
            devices_str = ";".join(
                [dev.to_protocol_string() for dev in self.devices.values()]
            )
            return f"OK {len(self.devices)} {devices_str}"


# ==================== SERVIDOR TCP ====================
class TCPServer:
    """
    Servidor TCP para comandos de control directo.
    Soporta múltiples clientes concurrentes mediante threading.
    """

    def __init__(self, device_manager: DeviceManager, host: str, port: int):
        self.device_manager = device_manager
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None

    def start(self):
        """Inicia el servidor TCP en un hilo separado"""
        self.running = True
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        print(f"[TCP] Servidor iniciado en {self.host}:{self.port}")

    def _run(self):
        """Loop principal del servidor TCP"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print(f"[TCP] Esperando conexiones en puerto {self.port}...")

        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[TCP] Cliente conectado desde {address}")

                # Crear hilo para manejar cliente
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True,
                )
                client_thread.start()

            except Exception as e:
                if self.running:
                    print(f"[TCP] Error aceptando conexión: {e}")

    def _handle_client(self, client_socket: socket.socket, address):
        """Maneja la comunicación con un cliente específico"""
        authenticated = False
        username = None

        try:
            # Enviar mensaje de bienvenida
            welcome_msg = (
                b"SERVIDOR DOMOTICO v2.0\n"
                b"Comandos: LOGIN, LIST, STATUS, SET, AUTO_OFF, "
                b"BRIGHTNESS, COLOR, CURTAINS, TEMP, LOG, EXIT\n"
            )
            client_socket.send(welcome_msg)

            while True:
                # Recibir comando
                data = client_socket.recv(1024).decode("utf-8").strip()
                if not data:
                    break

                print(f"[TCP] Comando recibido de {address}: {data}")

                # Procesar comando
                response = self._process_command(data, authenticated, username)

                # Actualizar autenticación si LOGIN fue exitoso
                if response.startswith("OK LOGIN"):
                    authenticated = True
                    username = data.split()[1] if len(data.split()) > 1 else "unknown"

                # Enviar respuesta
                client_socket.send((response + "\n").encode("utf-8"))

                # Salir si el cliente envía EXIT
                if data.upper() == "EXIT":
                    break

        except Exception as e:
            print(f"[TCP] Error con cliente {address}: {e}")
        finally:
            client_socket.close()
            print(f"[TCP] Cliente {address} desconectado")

    def _process_command(self, command: str, authenticated: bool, username: str) -> str:
        """
        Procesa los comandos del protocolo de texto.
        Retorna la respuesta correspondiente.
        """
        parts = command.split()
        if not parts:
            return "ERROR Comando vacío"

        cmd = parts[0].upper()

        # LOGIN <user> <pass>
        if cmd == "LOGIN":
            if len(parts) != 3:
                return "ERROR LOGIN: Uso: LOGIN <usuario> <contraseña>"
            user, password = parts[1], parts[2]
            if user in USUARIOS and USUARIOS[user] == password:
                return f"OK LOGIN Bienvenido {user}"
            return "ERROR LOGIN: Credenciales inválidas"

        # EXIT
        if cmd == "EXIT":
            return "OK Hasta pronto"

        # Comandos que NO requieren autenticación
        # LIST
        if cmd == "LIST":
            return self.device_manager.get_protocol_list()

        # STATUS <id>
        if cmd == "STATUS":
            if len(parts) != 2:
                return "ERROR STATUS: Uso: STATUS <device_id>"
            device_id = parts[1]
            device = self.device_manager.get_device(device_id)
            if device:
                return f"OK {device['id']} {device['estado']} {device['auto_off']}"
            return f"ERROR Dispositivo '{device_id}' no encontrado"

        # LOG
        if cmd == "LOG":
            logs = self.device_manager.get_log(20)
            return "OK LOG\n" + "\n".join(logs)

        # Comandos que SÍ requieren autenticación
        if not authenticated:
            return f"ERROR {cmd}: Requiere autenticación (usar LOGIN primero)"

        # SET <id> <ON|OFF> o SET <id> <BRIGHTNESS|COLOR> <value> o SET cortinas LEVEL <value> o SET termostato TEMP <value>
        if cmd == "SET":
            if len(parts) < 3:
                return "ERROR SET: Uso: SET <device_id> <ON|OFF|BRIGHTNESS|COLOR> [value] o SET cortinas LEVEL <0-100> o SET termostato TEMP <16-30>"

            device_id = parts[1]
            subcommand = parts[2].upper()

            # SET cortinas LEVEL <0-100> (también acepta persianas por compatibilidad)
            if device_id.lower() in ["persianas", "cortinas"]:
                if subcommand == "LEVEL" and len(parts) == 4:
                    try:
                        level = int(parts[3])
                        if level < 0 or level > 100:
                            return "ERROR SET: El nivel de cortinas debe estar entre 0 y 100"
                        device = self.device_manager.devices.get("cortinas")
                        if device:
                            device.curtains = level
                            device.ultimo_cambio = datetime.now().isoformat()
                            self.device_manager._add_log(
                                "cortinas", f"Posición ajustada a {level}%"
                            )
                            return f"OK SET cortinas LEVEL {level}"
                        return "ERROR Dispositivo cortinas no encontrado"
                    except ValueError:
                        return "ERROR SET: El nivel debe ser un número entero"
                return "ERROR SET: Uso: SET cortinas LEVEL <0-100>"

            # SET termostato TEMP <16-30> (también acepta clima por compatibilidad)
            if device_id.lower() in ["clima", "termostato"]:
                if subcommand == "TEMP" and len(parts) == 4:
                    try:
                        temp = float(parts[3])
                        if temp < 16 or temp > 30:
                            return (
                                "ERROR SET: La temperatura debe estar entre 16 y 30°C"
                            )
                        device = self.device_manager.devices.get("termostato")
                        if device:
                            device.target_temperature = temp
                            device.ultimo_cambio = datetime.now().isoformat()
                            self.device_manager._add_log(
                                "termostato", f"Temperatura objetivo: {temp}°C"
                            )
                            return f"OK SET termostato TEMP {temp}"
                        return "ERROR Dispositivo termostato no encontrado"
                    except ValueError:
                        return "ERROR SET: La temperatura debe ser un número"
                return "ERROR SET: Uso: SET termostato TEMP <16-30>"

            # SET <device_id> ON|OFF
            if subcommand in ["ON", "OFF"]:
                if self.device_manager.set_device_state(device_id, subcommand):
                    return f"OK SET {device_id} {subcommand}"
                return f"ERROR Dispositivo '{device_id}' no encontrado"

            # SET <device_id> BRIGHTNESS <0-100>
            if subcommand == "BRIGHTNESS":
                if len(parts) != 4:
                    return "ERROR SET: Uso: SET <device_id> BRIGHTNESS <0-100>"
                try:
                    brightness = int(parts[3])
                    if brightness < 0 or brightness > 100:
                        return "ERROR SET: El brillo debe estar entre 0 y 100"
                    if self.device_manager.set_brightness(device_id, brightness):
                        # Auto-encender si el brillo es > 0
                        if brightness > 0:
                            self.device_manager.set_device_state(device_id, "ON")
                        return f"OK SET {device_id} BRIGHTNESS {brightness}"
                    return (
                        f"ERROR Dispositivo '{device_id}' no encontrado o no es una luz"
                    )
                except ValueError:
                    return "ERROR SET: El brillo debe ser un número entero"

            # SET <device_id> COLOR <#RRGGBB>
            if subcommand == "COLOR":
                if len(parts) != 4:
                    return "ERROR SET: Uso: SET <device_id> COLOR <#RRGGBB>"
                color = parts[3]
                if not color.startswith("#") or len(color) != 7:
                    return "ERROR SET: El color debe estar en formato #RRGGBB"
                if self.device_manager.set_color(device_id, color):
                    return f"OK SET {device_id} COLOR {color}"
                return f"ERROR Dispositivo '{device_id}' no encontrado o no es una luz"

            return f"ERROR SET: Subcomando '{subcommand}' no reconocido. Use: ON, OFF, BRIGHTNESS, COLOR, LEVEL (persianas), TEMP (clima)"

        # AUTO_OFF <id> <segundos>
        if cmd == "AUTO_OFF":
            if len(parts) != 3:
                return "ERROR AUTO_OFF: Uso: AUTO_OFF <device_id> <segundos>"
            device_id = parts[1]
            try:
                segundos = int(parts[2])
                if segundos < 0:
                    return "ERROR AUTO_OFF: Los segundos deben ser >= 0"
                if self.device_manager.set_auto_off(device_id, segundos):
                    return f"OK AUTO_OFF {device_id} {segundos}s"
                return f"ERROR Dispositivo '{device_id}' no encontrado"
            except ValueError:
                return "ERROR AUTO_OFF: Los segundos deben ser un número entero"

        # BRIGHTNESS <id> <0-100>
        if cmd == "BRIGHTNESS":
            if len(parts) != 3:
                return "ERROR BRIGHTNESS: Uso: BRIGHTNESS <device_id> <0-100>"
            device_id = parts[1]
            try:
                brightness = int(parts[2])
                if brightness < 0 or brightness > 100:
                    return "ERROR BRIGHTNESS: El valor debe estar entre 0 y 100"
                if self.device_manager.set_brightness(device_id, brightness):
                    return f"OK BRIGHTNESS {device_id} {brightness}"
                return f"ERROR Dispositivo '{device_id}' no encontrado o no es una luz"
            except ValueError:
                return "ERROR BRIGHTNESS: El valor debe ser un número entero"

        # COLOR <id> <#RRGGBB>
        if cmd == "COLOR":
            if len(parts) != 3:
                return "ERROR COLOR: Uso: COLOR <device_id> <#RRGGBB>"
            device_id = parts[1]
            color = parts[2]
            if not color.startswith("#") or len(color) != 7:
                return "ERROR COLOR: El color debe estar en formato #RRGGBB"
            if self.device_manager.set_color(device_id, color):
                return f"OK COLOR {device_id} {color}"
            return f"ERROR Dispositivo '{device_id}' no encontrado o no es una luz"

        # CURTAINS <0-100>
        if cmd == "CURTAINS":
            if len(parts) != 2:
                return "ERROR CURTAINS: Uso: CURTAINS <0-100>"
            try:
                curtains = int(parts[1])
                if curtains < 0 or curtains > 100:
                    return "ERROR CURTAINS: El valor debe estar entre 0 y 100"
                if self.device_manager.set_curtains(curtains):
                    return f"OK CURTAINS {curtains}"
                return "ERROR No se pudo ajustar las cortinas"
            except ValueError:
                return "ERROR CURTAINS: El valor debe ser un número entero"

        # TEMP <temperatura>
        if cmd == "TEMP":
            if len(parts) != 2:
                return "ERROR TEMP: Uso: TEMP <16-30>"
            try:
                temp = float(parts[1])
                if temp < 16 or temp > 30:
                    return "ERROR TEMP: La temperatura debe estar entre 16 y 30°C"
                if self.device_manager.set_temperature(temp):
                    return f"OK TEMP {temp}"
                return "ERROR No se pudo ajustar la temperatura"
            except ValueError:
                return "ERROR TEMP: La temperatura debe ser un número"

        return f"ERROR Comando '{cmd}' no reconocido"

    def stop(self):
        """Detiene el servidor TCP"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


# ==================== SERVIDOR UDP (BROADCAST) ====================
class UDPBroadcaster:
    """
    Servidor UDP que transmite el estado de la casa cada N segundos.
    Útil para monitorización pasiva y telemetría.
    """

    def __init__(self, device_manager: DeviceManager, port: int, interval: int):
        self.device_manager = device_manager
        self.port = port
        self.interval = interval
        self.running = False

    def start(self):
        """Inicia el broadcaster en un hilo separado"""
        self.running = True
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        print(
            f"[UDP] Broadcaster iniciado en puerto {self.port} (cada {self.interval}s)"
        )

    def _run(self):
        """Loop de broadcast periódico"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.running:
            try:
                # Obtener estado actual
                devices = self.device_manager.get_all_devices()
                payload = json.dumps(
                    {"timestamp": datetime.now().isoformat(), "devices": devices}
                )

                # Broadcast
                sock.sendto(payload.encode("utf-8"), ("<broadcast>", self.port))
                print(f"[UDP] Broadcast enviado ({len(devices)} dispositivos)")

            except Exception as e:
                print(f"[UDP] Error en broadcast: {e}")

            time.sleep(self.interval)

        sock.close()

    def stop(self):
        """Detiene el broadcaster"""
        self.running = False


# ==================== API REST (GEMELO DIGITAL) ====================
def create_api(device_manager: DeviceManager) -> Flask:
    """
    Crea la aplicación Flask con endpoints JSON para el gemelo digital.
    Permite integración con frontends web y aplicaciones móviles.
    """
    app = Flask(__name__)
    CORS(app)  # Permitir CORS para desarrollo web

    @app.route("/api/status", methods=["GET"])
    def get_status():
        """GET /api/status - Retorna el estado completo de la casa"""
        devices = device_manager.get_all_devices()
        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "devices": devices,
                "total": len(devices),
            }
        )

    @app.route("/api/device/<device_id>", methods=["GET"])
    def get_device(device_id):
        """GET /api/device/<id> - Retorna estado de un dispositivo"""
        device = device_manager.get_device(device_id)
        if device:
            return jsonify({"success": True, "device": device})
        return jsonify({"success": False, "error": "Dispositivo no encontrado"}), 404

    @app.route("/api/control", methods=["POST"])
    def control():
        """
        POST /api/control - Controla dispositivos
        Body JSON: {"id": "luz_salon", "action": "ON"|"OFF"}
        """
        data = request.get_json()
        if not data or "id" not in data or "action" not in data:
            return jsonify({"success": False, "error": "Formato inválido"}), 400

        device_id = data["id"]
        action = data["action"].upper()

        if action not in ["ON", "OFF"]:
            return jsonify({"success": False, "error": "Acción debe ser ON u OFF"}), 400

        if device_manager.set_device_state(device_id, action):
            return jsonify(
                {"success": True, "device_id": device_id, "new_state": action}
            )
        return jsonify({"success": False, "error": "Dispositivo no encontrado"}), 404

    @app.route("/api/auto_off", methods=["POST"])
    def auto_off():
        """
        POST /api/auto_off - Configura autoapagado
        Body JSON: {"id": "luz_salon", "seconds": 10}
        """
        data = request.get_json()
        if not data or "id" not in data or "seconds" not in data:
            return jsonify({"success": False, "error": "Formato inválido"}), 400

        device_id = data["id"]
        try:
            seconds = int(data["seconds"])
            if seconds < 0:
                return jsonify(
                    {"success": False, "error": "Segundos deben ser >= 0"}
                ), 400

            if device_manager.set_auto_off(device_id, seconds):
                return jsonify(
                    {
                        "success": True,
                        "device_id": device_id,
                        "auto_off_seconds": seconds,
                    }
                )
            return jsonify(
                {"success": False, "error": "Dispositivo no encontrado"}
            ), 404

        except ValueError:
            return jsonify(
                {"success": False, "error": "Segundos debe ser un número"}
            ), 400

    @app.route("/api/log", methods=["GET"])
    def get_log():
        """GET /api/log - Retorna historial de eventos"""
        limit = request.args.get("limit", 20, type=int)
        logs = device_manager.get_log(limit)
        return jsonify({"success": True, "logs": logs, "count": len(logs)})

    @app.route("/api/brightness", methods=["POST"])
    def set_brightness():
        """POST /api/brightness - Ajustar brillo de luz
        Body JSON: {"id": "luz_salon", "brightness": 75}
        """
        data = request.get_json()
        if not data or "id" not in data or "brightness" not in data:
            return jsonify({"success": False, "error": "Formato inválido"}), 400

        device_id = data["id"]
        try:
            brightness = int(data["brightness"])
            if brightness < 0 or brightness > 100:
                return jsonify(
                    {"success": False, "error": "Brillo debe estar entre 0 y 100"}
                ), 400

            if device_manager.set_brightness(device_id, brightness):
                return jsonify(
                    {"success": True, "device_id": device_id, "brightness": brightness}
                )
            return jsonify(
                {"success": False, "error": "Dispositivo no encontrado o no es una luz"}
            ), 404
        except ValueError:
            return jsonify(
                {"success": False, "error": "Brillo debe ser un número"}
            ), 400

    @app.route("/api/color", methods=["POST"])
    def set_color():
        """POST /api/color - Ajustar color de luz
        Body JSON: {"id": "luz_salon", "color": "#ff0000"}
        """
        data = request.get_json()
        if not data or "id" not in data or "color" not in data:
            return jsonify({"success": False, "error": "Formato inválido"}), 400

        device_id = data["id"]
        color = data["color"]

        if not color.startswith("#") or len(color) != 7:
            return jsonify(
                {"success": False, "error": "Color debe estar en formato #RRGGBB"}
            ), 400

        if device_manager.set_color(device_id, color):
            return jsonify({"success": True, "device_id": device_id, "color": color})
        return jsonify(
            {"success": False, "error": "Dispositivo no encontrado o no es una luz"}
        ), 404

    @app.route("/api/curtains", methods=["POST"])
    def set_curtains():
        """POST /api/curtains - Ajustar posición de cortinas
        Body JSON: {"position": 50}
        """
        data = request.get_json()
        if not data or "position" not in data:
            return jsonify({"success": False, "error": "Formato inválido"}), 400

        try:
            position = int(data["position"])
            if position < 0 or position > 100:
                return jsonify(
                    {"success": False, "error": "Posición debe estar entre 0 y 100"}
                ), 400

            if device_manager.set_curtains(position):
                return jsonify({"success": True, "position": position})
            return jsonify(
                {"success": False, "error": "No se pudo ajustar las cortinas"}
            ), 500
        except ValueError:
            return jsonify(
                {"success": False, "error": "Posición debe ser un número"}
            ), 400

    @app.route("/api/temperature", methods=["POST"])
    def set_temperature():
        """POST /api/temperature - Ajustar temperatura objetivo
        Body JSON: {"temperature": 22}
        """
        data = request.get_json()
        if not data or "temperature" not in data:
            return jsonify({"success": False, "error": "Formato inválido"}), 400

        try:
            temp = float(data["temperature"])
            if temp < 16 or temp > 30:
                return jsonify(
                    {
                        "success": False,
                        "error": "Temperatura debe estar entre 16 y 30°C",
                    }
                ), 400

            if device_manager.set_temperature(temp):
                return jsonify({"success": True, "temperature": temp})
            return jsonify(
                {"success": False, "error": "No se pudo ajustar la temperatura"}
            ), 500
        except ValueError:
            return jsonify(
                {"success": False, "error": "Temperatura debe ser un número"}
            ), 400

    @app.route("/", methods=["GET"])
    def index():
        """Página de información de la API"""
        return jsonify(
            {
                "name": "Sistema Domótico - API REST",
                "version": "2.0",
                "endpoints": {
                    "GET /api/status": "Estado de todos los dispositivos",
                    "GET /api/device/<id>": "Estado de un dispositivo",
                    "POST /api/control": "Controlar dispositivo (ON/OFF)",
                    "POST /api/auto_off": "Configurar autoapagado",
                    "POST /api/brightness": "Ajustar brillo de luz",
                    "POST /api/color": "Ajustar color de luz",
                    "POST /api/curtains": "Ajustar posición de cortinas",
                    "POST /api/temperature": "Ajustar temperatura objetivo",
                    "GET /api/log": "Historial de eventos",
                },
            }
        )

    return app


# ==================== SERVIDOR PRINCIPAL ====================
class DomoticServer:
    """
    Servidor principal que orquesta todos los componentes del sistema.
    """

    def __init__(self):
        self.device_manager = DeviceManager()
        self.tcp_server = TCPServer(self.device_manager, TCP_HOST, TCP_PORT)
        self.udp_broadcaster = UDPBroadcaster(
            self.device_manager, UDP_PORT, BROADCAST_INTERVAL
        )
        self.flask_app = create_api(self.device_manager)

    def start(self):
        """Inicia todos los servicios del servidor"""
        print("=" * 60)
        print("SISTEMA DOMÓTICO - SERVIDOR CENTRAL")
        print("=" * 60)

        # Iniciar servidor TCP
        self.tcp_server.start()

        # Iniciar broadcaster UDP
        self.udp_broadcaster.start()

        # Iniciar API REST en hilo separado
        api_thread = threading.Thread(
            target=lambda: self.flask_app.run(
                host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False
            ),
            daemon=True,
        )
        api_thread.start()
        print(f"[API] Servidor REST iniciado en puerto {API_PORT}")

        print("\n" + "=" * 60)
        print("SERVIDOR LISTO - Servicios activos:")
        print(f"  - TCP (Comandos): puerto {TCP_PORT}")
        print(f"  - UDP (Telemetría): puerto {UDP_PORT}")
        print(f"  - API REST (Gemelo Digital): puerto {API_PORT}")
        print("=" * 60)
        print("\nPresiona Ctrl+C para detener el servidor\n")

        # Mantener el programa vivo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nDeteniendo servidor...")
            self.stop()

    def stop(self):
        """Detiene todos los servicios"""
        self.tcp_server.stop()
        self.udp_broadcaster.stop()
        print("Servidor detenido correctamente")


# ==================== PUNTO DE ENTRADA ====================
if __name__ == "__main__":
    server = DomoticServer()
    server.start()
