#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Domótico - Cliente de Consola Interactivo
==================================================
Cliente TCP para interactuar con el servidor domótico.
Proporciona un menú CLI para probar todas las funcionalidades.

Uso: python client_console.py [host] [puerto]
"""

import socket
import sys
import os

# Configuración por defecto
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5000


class DomoticClient:
    """Cliente de consola para el sistema domótico"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.authenticated = False
        self.username = None

    def connect(self) -> bool:
        """Establece conexión con el servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Timeout de 10 segundos
            self.socket.connect((self.host, self.port))
            self.connected = True

            # Leer mensaje de bienvenida
            welcome = self.socket.recv(4096).decode("utf-8")
            print("\n" + "=" * 60)
            print(welcome)
            print("=" * 60 + "\n")

            return True

        except ConnectionRefusedError:
            print(
                f"❌ Error: No se pudo conectar al servidor en {self.host}:{self.port}"
            )
            print("   ¿El servidor está en ejecución?")
            return False
        except socket.timeout:
            print("❌ Error: Timeout al conectar con el servidor")
            return False
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False

    def send_command(self, command: str) -> str:
        """
        Envía un comando al servidor y retorna la respuesta.
        Maneja la comunicación de bajo nivel.
        """
        if not self.connected:
            return "ERROR: No conectado al servidor"

        try:
            # Enviar comando (agregar \n si no lo tiene)
            if not command.endswith("\n"):
                command += "\n"
            self.socket.send(command.encode("utf-8"))

            # Recibir respuesta
            response = self.socket.recv(4096).decode("utf-8").strip()
            return response

        except socket.timeout:
            return "ERROR: Timeout esperando respuesta del servidor"
        except Exception as e:
            self.connected = False
            return f"ERROR: Conexión perdida - {e}"

    def login(self):
        """Maneja el proceso de autenticación"""
        print("\n🔐 AUTENTICACIÓN")
        print("-" * 60)
        print("Usuarios de prueba:")
        print("  - admin / admin123")
        print("  - user / pass123")
        print("-" * 60)

        username = input("Usuario: ").strip()
        password = input("Contraseña: ").strip()

        if not username or not password:
            print("❌ Usuario y contraseña no pueden estar vacíos")
            return

        response = self.send_command(f"LOGIN {username} {password}")
        print(f"\n📡 Respuesta: {response}\n")

        if response.startswith("OK LOGIN"):
            self.authenticated = True
            self.username = username
            print(f"✅ Autenticado como: {username}")
        else:
            print("❌ Autenticación fallida")

    def list_devices(self):
        """Lista todos los dispositivos con todos sus parámetros"""
        print("\n📋 LISTADO COMPLETO DE DISPOSITIVOS")
        print("=" * 100)

        response = self.send_command("LIST")

        if response.startswith("OK"):
            parts = response.split(maxsplit=2)
            if len(parts) >= 3:
                count = parts[1]
                devices_str = parts[2]

                print(f"Total de dispositivos: {count}\n")

                for device_data in devices_str.split(";"):
                    device_info = device_data.split(",")
                    if len(device_info) >= 8:
                        (
                            dev_id,
                            estado,
                            auto_off,
                            brightness,
                            color,
                            curtains,
                            temp,
                            target_temp,
                        ) = device_info[:8]

                        # Emoji según el tipo y estado
                        if "luz" in dev_id:
                            emoji = "💡"
                        elif "tv" in dev_id:
                            emoji = "📺"
                        elif "calefactor" in dev_id:
                            emoji = "🔥"
                        elif "cortinas" in dev_id:
                            emoji = "🪟"
                        elif "termostato" in dev_id:
                            emoji = "🌡️"
                        else:
                            emoji = "🔌"

                        estado_emoji = "🟢" if estado == "ON" else "⚫"
                        auto_info = f"{auto_off}s" if auto_off != "0" else "--"

                        print(f"{emoji} {estado_emoji} {dev_id:<20}")
                        if "cortinas" not in dev_id and "termostato" not in dev_id:
                            print(
                                f"   └─ Estado: {estado:<5} | Auto-Off: {auto_info:<8}"
                            )

                        if "luz" in dev_id:
                            print(f"   └─ Brillo: {brightness}% | Color: {color}")
                        elif "cortinas" in dev_id:
                            print(f"   └─ Posición: {curtains}% abierto")
                        elif "termostato" in dev_id:
                            print(
                                f"   └─ Temperatura: {temp}°C → Objetivo: {target_temp}°C"
                            )

                        print()
            else:
                print("Formato de respuesta inesperado")
        else:
            print(f"❌ Error: {response}")
        print("=" * 100)

    def get_status(self):
        """Obtiene el estado de un dispositivo específico"""
        print("\n📊 ESTADO DE DISPOSITIVO")
        print("-" * 60)

        device_id = input("ID del dispositivo: ").strip()
        if not device_id:
            print("❌ ID no puede estar vacío")
            return

        response = self.send_command(f"STATUS {device_id}")

        if response.startswith("OK"):
            parts = response.split()
            if len(parts) >= 4:
                dev_id, estado, auto_off = parts[1], parts[2], parts[3]

                print(f"\n🔍 Dispositivo: {dev_id}")
                print(f"   Estado: {estado} {'🟢' if estado == 'ON' else '⚫'}")
                print(
                    f"   Auto-Off: {auto_off}s {'(Activo)' if auto_off != '0' else '(Desactivado)'}"
                )
        else:
            print(f"❌ {response}")

        print()

    def set_device(self):
        """Modo guiado completo para cambiar parámetros de dispositivos (requiere autenticación)"""
        if not self.authenticated:
            print("\n❌ Esta función requiere autenticación.")
            print("   Por favor, use la opción 1 (Login) primero.\n")
            return

        print("\n⚙️  MODO GUIADO - CONTROL DE DISPOSITIVOS Y PARÁMETROS")
        print("=" * 80)
        print("\n¿Qué deseas controlar?\n")
        print("  1. 💡 Luz del salón (ON/OFF)")
        print("  2. 🔆 Brillo de la luz (0-100%)")
        print("  3. 🎨 Color de la luz (#RRGGBB)")
        print("  4. 📺 TV (ON/OFF)")
        print("  5. 🔥 Calefactor (ON/OFF)")
        print("  6. 🪟 Cortinas - Posición (0-100%)")
        print("  7. 🌡️  Termostato - Temperatura objetivo (16-30°C)")
        print("  0. ↩️  Cancelar")
        print()

        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            # Luz ON/OFF
            print("\n💡 CONTROL DE LUZ DEL SALÓN")
            print("-" * 60)
            estado = input("Estado (ON/OFF): ").strip().upper()
            if estado in ["ON", "OFF"]:
                response = self.send_command(f"SET luz_salon {estado}")
                if response.startswith("OK"):
                    emoji = "🟢" if estado == "ON" else "⚫"
                    print(f"\n✅ {emoji} Luz del salón: {estado}")
                else:
                    print(f"\n❌ {response}")
            else:
                print("❌ Estado inválido (debe ser ON u OFF)")

        elif opcion == "2":
            # Brillo
            print("\n🔆 AJUSTAR BRILLO DE LA LUZ")
            print("-" * 60)
            print("Nivel de brillo actual: (ver con opción 2 del menú)")
            brillo = input("Nuevo brillo (0-100): ").strip()
            try:
                brillo_val = int(brillo)
                if 0 <= brillo_val <= 100:
                    response = self.send_command(
                        f"SET luz_salon BRIGHTNESS {brillo_val}"
                    )
                    if response.startswith("OK"):
                        bar = "█" * (brillo_val // 5) + "░" * (20 - brillo_val // 5)
                        print(f"\n✅ Brillo ajustado: {brillo_val}%")
                        print(f"   [{bar}]")
                    else:
                        print(f"\n❌ {response}")
                else:
                    print("❌ El brillo debe estar entre 0 y 100")
            except ValueError:
                print("❌ Valor inválido")

        elif opcion == "3":
            # Color
            print("\n🎨 CAMBIAR COLOR DE LA LUZ")
            print("-" * 60)
            print("Colores predefinidos:")
            print("  1. Blanco (#ffffff)")
            print("  2. Cálido (#ffd699)")
            print("  3. Azul (#0066ff)")
            print("  4. Rojo (#ff0000)")
            print("  5. Verde (#00ff00)")
            print("  6. Personalizado")

            color_opcion = input("\nSelecciona: ").strip()
            colores = {
                "1": "#ffffff",
                "2": "#ffd699",
                "3": "#0066ff",
                "4": "#ff0000",
                "5": "#00ff00",
            }

            if color_opcion in colores:
                color = colores[color_opcion]
            elif color_opcion == "6":
                color = input("Ingresa color en formato #RRGGBB: ").strip()
            else:
                print("❌ Opción inválida")
                return

            if color.startswith("#") and len(color) == 7:
                response = self.send_command(f"SET luz_salon COLOR {color}")
                if response.startswith("OK"):
                    print(f"\n✅ Color cambiado a: {color}")
                else:
                    print(f"\n❌ {response}")
            else:
                print("❌ Formato de color inválido (debe ser #RRGGBB)")

        elif opcion == "4":
            # TV
            print("\n📺 CONTROL DE TV")
            print("-" * 60)
            estado = input("Estado (ON/OFF): ").strip().upper()
            if estado in ["ON", "OFF"]:
                response = self.send_command(f"SET enchufe_tv {estado}")
                if response.startswith("OK"):
                    emoji = "🟢" if estado == "ON" else "⚫"
                    print(f"\n✅ {emoji} TV: {estado}")
                else:
                    print(f"\n❌ {response}")
            else:
                print("❌ Estado inválido")

        elif opcion == "5":
            # Calefactor
            print("\n🔥 CONTROL DE CALEFACTOR")
            print("-" * 60)
            estado = input("Estado (ON/OFF): ").strip().upper()
            if estado in ["ON", "OFF"]:
                response = self.send_command(f"SET enchufe_calefactor {estado}")
                if response.startswith("OK"):
                    emoji = "🟢" if estado == "ON" else "⚫"
                    print(f"\n✅ {emoji} Calefactor: {estado}")
                else:
                    print(f"\n❌ {response}")
            else:
                print("❌ Estado inválido")

        elif opcion == "6":
            # Cortinas
            print("\n🪟 AJUSTAR CORTINAS")
            print("-" * 60)
            print("  0% = Completamente cerradas")
            print("100% = Completamente abiertas")
            posicion = input("\nPosición (0-100): ").strip()
            try:
                pos_val = int(posicion)
                if 0 <= pos_val <= 100:
                    response = self.send_command(f"SET cortinas LEVEL {pos_val}")
                    if response.startswith("OK"):
                        bar = "█" * (pos_val // 5) + "░" * (20 - pos_val // 5)
                        print(f"\n✅ Cortinas ajustadas: {pos_val}%")
                        print(f"   [{bar}]")
                    else:
                        print(f"\n❌ {response}")
                else:
                    print("❌ La posición debe estar entre 0 y 100")
            except ValueError:
                print("❌ Valor inválido")

        elif opcion == "7":
            # Temperatura
            print("\n🌡️  AJUSTAR TEMPERATURA OBJETIVO DEL TERMOSTATO")
            print("-" * 60)
            print("Rango permitido: 16°C - 30°C")
            temp = input("\nTemperatura deseada: ").strip()
            try:
                temp_val = float(temp)
                if 16 <= temp_val <= 30:
                    response = self.send_command(f"SET termostato TEMP {temp_val}")
                    if response.startswith("OK"):
                        print(f"\n✅ Temperatura objetivo del termostato: {temp_val}°C")
                    else:
                        print(f"\n❌ {response}")
                else:
                    print("❌ La temperatura debe estar entre 16 y 30°C")
            except ValueError:
                print("❌ Valor inválido")

        elif opcion == "0":
            print("\n↩️  Cancelado")
            return
        else:
            print("\n❌ Opción no válida")

        print()

    def set_auto_off(self):
        """Configura el autoapagado (requiere autenticación)"""
        if not self.authenticated:
            print("\n❌ Esta función requiere autenticación.")
            print("   Por favor, use la opción 1 (Login) primero.\n")
            return

        print("\n⏰ CONFIGURAR AUTO-APAGADO")
        print("-" * 60)

        device_id = input("ID del dispositivo: ").strip()
        segundos_str = input("Segundos para apagar (0 = desactivar): ").strip()

        if not device_id or not segundos_str:
            print("❌ Entrada inválida")
            return

        try:
            segundos = int(segundos_str)
            if segundos < 0:
                print("❌ Los segundos deben ser >= 0")
                return
        except ValueError:
            print("❌ Segundos debe ser un número entero")
            return

        response = self.send_command(f"AUTO_OFF {device_id} {segundos}")

        if response.startswith("OK"):
            if segundos > 0:
                print(
                    f"\n✅ ⏰ Auto-apagado configurado: '{device_id}' se apagará en {segundos}s"
                )
            else:
                print(f"\n✅ Auto-apagado desactivado para '{device_id}'")
        else:
            print(f"\n❌ {response}")

        print()

    def view_log(self):
        """Muestra el historial de eventos"""
        print("\n📜 HISTORIAL DE EVENTOS")
        print("-" * 60)

        response = self.send_command("LOG")

        if response.startswith("OK LOG"):
            lines = response.split("\n")[1:]  # Saltar primera línea "OK LOG"
            if lines:
                for line in lines:
                    if line.strip():
                        print(f"  {line}")
            else:
                print("  (Sin eventos registrados)")
        else:
            print(f"❌ {response}")

        print()

    def send_custom_command(self):
        """Permite enviar un comando personalizado"""
        print("\n⌨️  COMANDO PERSONALIZADO")
        print("-" * 60)

        command = input("Comando: ").strip()
        if not command:
            print("❌ Comando vacío")
            return

        response = self.send_command(command)
        print(f"\n📡 Respuesta:\n{response}\n")

    def show_menu(self):
        """Muestra el menú principal"""
        status_auth = (
            f"✅ {self.username}" if self.authenticated else "❌ No autenticado"
        )

        print("\n" + "=" * 60)
        print("               SISTEMA DOMÓTICO - CLIENTE")
        print("=" * 60)
        print(f"Servidor: {self.host}:{self.port}")
        print(f"Estado: {'🟢 Conectado' if self.connected else '🔴 Desconectado'}")
        print(f"Autenticación: {status_auth}")
        print("=" * 60)
        print("\n📋 MENÚ DE OPCIONES:")
        print()
        print("  1. 🔐 Login (Autenticación)")
        print("  2. 📋 Listar todos los dispositivos")
        print("  3. 📊 Ver estado de un dispositivo")
        print("  4. 💡 Encender/Apagar dispositivo (requiere login)")
        print("  5. ⏰ Configurar auto-apagado (requiere login)")
        print("  6. 📜 Ver historial de eventos")
        print("  7. ⌨️  Enviar comando personalizado")
        print("  8. 🔄 Reconectar al servidor")
        print("  0. ❌ Salir")
        print()

    def reconnect(self):
        """Reconecta al servidor"""
        print("\n🔄 Reconectando...")
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass

        self.connected = False
        self.authenticated = False
        self.username = None

        if self.connect():
            print("✅ Reconexión exitosa\n")
        else:
            print("❌ Reconexión fallida\n")

    def run(self):
        """Loop principal del cliente"""
        # Intentar conectar
        if not self.connect():
            print("\n💡 Asegúrate de que el servidor esté ejecutándose:")
            print("   python server_domotico.py\n")
            return

        # Menú interactivo
        while True:
            self.show_menu()

            try:
                opcion = input("Seleccione una opción: ").strip()

                if opcion == "1":
                    self.login()
                elif opcion == "2":
                    self.list_devices()
                elif opcion == "3":
                    self.get_status()
                elif opcion == "4":
                    self.set_device()
                elif opcion == "5":
                    self.set_auto_off()
                elif opcion == "6":
                    self.view_log()
                elif opcion == "7":
                    self.send_custom_command()
                elif opcion == "8":
                    self.reconnect()
                elif opcion == "0":
                    print("\n👋 Cerrando cliente...\n")
                    break
                else:
                    print("\n❌ Opción no válida\n")

                # Pausa para leer la salida
                if opcion in ["1", "2", "3", "4", "5", "6", "7"]:
                    input("\nPresione Enter para continuar...")

            except KeyboardInterrupt:
                print("\n\n👋 Interrumpido por el usuario\n")
                break
            except EOFError:
                print("\n\n👋 Cerrando cliente...\n")
                break

        # Cerrar conexión
        if self.socket:
            try:
                self.send_command("EXIT")
                self.socket.close()
            except Exception:
                pass

        print("Cliente cerrado correctamente.\n")

    def disconnect(self):
        """Cierra la conexión"""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        self.connected = False
        self.authenticated = False


# ==================== PUNTO DE ENTRADA ====================
def main():
    """Función principal"""
    # Limpiar consola
    os.system("cls" if os.name == "nt" else "clear")

    # Obtener host y puerto desde argumentos o usar valores por defecto
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"❌ Puerto inválido: {sys.argv[2]}")
            print(f"Usando puerto por defecto: {DEFAULT_PORT}")

    # Banner
    print("\n" + "=" * 60)
    print("     CLIENTE CONSOLA - SISTEMA DOMÓTICO")
    print("=" * 60)
    print(f"\nConectando a: {host}:{port}\n")

    # Crear y ejecutar cliente
    client = DomoticClient(host, port)

    try:
        client.run()
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
