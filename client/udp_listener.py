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


def format_devices_table(devices):
    """Formatea los dispositivos en una tabla legible"""
    lines = []

    # Encabezado
    header = f"{'ID':<20} {'Tipo':<12} {'Estado':<8} {'Auto-Off':<10} {'Parámetros'}"
    lines.append(header)
    lines.append("=" * 100)

    for device in devices:
        dev_id = device["id"]
        dev_type = device["type"]
        estado = device.get("estado", "N/A")
        auto_off = device.get("auto_off", 0)

        # Auto-off solo si aplica
        auto_off_str = f"{auto_off}s" if auto_off > 0 else "--"

        # Parámetros específicos según tipo
        params = []

        if dev_type == "luz":
            brightness = device.get("brightness", 0)
            color = device.get("color", "#ffffff")
            params.append(f"Brillo: {brightness}%")
            params.append(f"Color: {color}")

        elif dev_type == "cortinas":
            curtains = device.get("curtains", 0)
            params.append(f"Posición: {curtains}%")
            estado = "--"  # Cortinas no tienen estado ON/OFF
            auto_off_str = "--"

        elif dev_type == "termostato":
            temp = device.get("temperature", 0)
            target_temp = device.get("target_temperature", 0)
            params.append(f"Actual: {temp}°C")
            params.append(f"Objetivo: {target_temp}°C")
            estado = "--"  # Termostato no tiene estado ON/OFF
            auto_off_str = "--"

        params_str = " | ".join(params) if params else "--"

        line = (
            f"{dev_id:<20} {dev_type:<12} {estado:<8} {auto_off_str:<10} {params_str}"
        )
        lines.append(line)

    return "\n".join(lines)


def listen_udp_telemetry(port):
    """
    Escucha el broadcast UDP de telemetría y muestra los datos
    """
    print("=" * 100)
    print("LISTENER DE TELEMETRÍA UDP - SISTEMA DOMÓTICO")
    print("=" * 100)
    print(f"\nEscuchando broadcast en puerto {port}...")
    print("Esperando paquetes UDP...")
    print("\nPresiona Ctrl+C para detener\n")

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
                print("\n" + "=" * 100)
                print(
                    f"Paquete #{packet_count} | Origen: {addr[0]}:{addr[1]} | Timestamp: {server_time}"
                )
                print(f"Total dispositivos: {len(devices)}")
                print("=" * 100)

                if devices:
                    print("\n" + format_devices_table(devices))
                else:
                    print("\nNo hay dispositivos registrados")

                print("\n" + "=" * 100)
                local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Recibido localmente: {local_time}")
                print()

            except json.JSONDecodeError:
                print(f"Error decodificando JSON desde {addr}")
            except Exception as e:
                print(f"Error procesando paquete: {e}")

    except KeyboardInterrupt:
        print("\n\nListener detenido por el usuario")
    except Exception as e:
        print(f"\nError en listener: {e}")
    finally:
        sock.close()
        print(f"\nTotal de paquetes recibidos: {packet_count}")
        print("Socket UDP cerrado correctamente\n")


def main():
    """Función principal"""
    port = DEFAULT_PORT

    # Leer puerto desde argumentos
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Puerto inválido: {sys.argv[1]}")
            print(f"Usando puerto por defecto: {DEFAULT_PORT}")
            port = DEFAULT_PORT

    listen_udp_telemetry(port)


if __name__ == "__main__":
    main()
