#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Listener de Telemetría UDP
==========================
Cliente UDP que escucha el broadcast de telemetría del servidor domótico.
Muestra el estado de los dispositivos en tiempo real sin conexión TCP.

Uso: python udp_listener.py [puerto]
"""

import socket
import json
import sys
from datetime import datetime

DEFAULT_PORT = 5001


def format_device_info(device):
    """Formatea la información de un dispositivo de forma legible"""
    emoji = "💡" if device["type"] == "luz" else "🔌"
    estado_emoji = "🟢" if device["estado"] == "ON" else "⚫"

    auto_off_info = ""
    if device["auto_off"] > 0:
        auto_off_info = f" [Auto-off: {device['auto_off']}s]"

    return f"{emoji} {device['id']:<20} {estado_emoji} {device['estado']:<5}{auto_off_info}"


def listen_udp_telemetry(port):
    """
    Escucha el broadcast UDP de telemetría y muestra los datos
    """
    print("=" * 70)
    print("           LISTENER DE TELEMETRÍA UDP - SISTEMA DOMÓTICO")
    print("=" * 70)
    print(f"\n📡 Escuchando broadcast en puerto {port}...")
    print("🔄 Esperando paquetes UDP...\n")
    print("Presiona Ctrl+C para detener\n")

    # Crear socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Permitir broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind al puerto
    sock.bind(("", port))

    packet_count = 0

    try:
        while True:
            # Recibir datos
            data, addr = sock.recvfrom(4096)
            packet_count += 1

            try:
                # Decodificar JSON
                payload = json.loads(data.decode("utf-8"))

                # Timestamp del servidor
                server_time = payload.get("timestamp", "N/A")
                devices = payload.get("devices", [])

                # Limpiar pantalla (comentar si no deseas limpiar)
                # print('\033[2J\033[H', end='')

                # Mostrar información
                print("\n" + "=" * 70)
                print(f"📦 Paquete #{packet_count} recibido desde {addr[0]}:{addr[1]}")
                print(f"🕐 Timestamp del servidor: {server_time}")
                print(f"🏠 Dispositivos en la casa: {len(devices)}")
                print("=" * 70)

                if devices:
                    print(f"\n{'Dispositivo':<30} {'Estado':<15} {'Info'}")
                    print("-" * 70)
                    for device in devices:
                        print(format_device_info(device))
                else:
                    print("\n⚠️  No hay dispositivos registrados")

                print("-" * 70)
                local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"🕐 Recibido localmente: {local_time}")
                print()

            except json.JSONDecodeError:
                print(f"⚠️  Error decodificando JSON desde {addr}")
            except Exception as e:
                print(f"❌ Error procesando paquete: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Listener detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en listener: {e}")
    finally:
        sock.close()
        print(f"\n📊 Total de paquetes recibidos: {packet_count}")
        print("Socket UDP cerrado correctamente\n")


def main():
    """Función principal"""
    port = DEFAULT_PORT

    # Leer puerto desde argumentos
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ Puerto inválido: {sys.argv[1]}")
            print(f"Usando puerto por defecto: {DEFAULT_PORT}")
            port = DEFAULT_PORT

    listen_udp_telemetry(port)


if __name__ == "__main__":
    main()
