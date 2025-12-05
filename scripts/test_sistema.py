#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Pruebas Automatizadas
================================
Ejecuta una batería de pruebas contra el servidor domótico para
verificar que todas las funcionalidades operan correctamente.

Requisitos: El servidor debe estar ejecutándose antes de lanzar este script.

Uso: python test_sistema.py
"""

import socket
import time
import requests
from datetime import datetime

# Configuración
TCP_HOST = "localhost"
TCP_PORT = 5000
API_BASE = "http://localhost:8080/api"

# Colores ANSI para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class TestRunner:
    """Ejecutor de pruebas del sistema domótico"""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tcp_socket = None

    def print_header(self, text):
        """Imprime encabezado de sección"""
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{BLUE}{text.center(70)}{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}\n")

    def print_test(self, name, passed, details=""):
        """Imprime resultado de un test"""
        if passed:
            print(f"{GREEN}✅ PASS{RESET} - {name}")
            if details:
                print(f"         {details}")
            self.tests_passed += 1
        else:
            print(f"{RED}❌ FAIL{RESET} - {name}")
            if details:
                print(f"         {details}")
            self.tests_failed += 1

    def connect_tcp(self):
        """Conecta al servidor TCP"""
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(5)
            self.tcp_socket.connect((TCP_HOST, TCP_PORT))

            # Leer mensaje de bienvenida
            welcome = self.tcp_socket.recv(4096).decode("utf-8")
            return True, welcome
        except Exception as e:
            return False, str(e)

    def send_tcp_command(self, command):
        """Envía comando TCP y retorna respuesta"""
        try:
            self.tcp_socket.send((command + "\n").encode("utf-8"))
            response = self.tcp_socket.recv(4096).decode("utf-8").strip()
            return response
        except Exception as e:
            return f"ERROR: {e}"

    def test_tcp_connection(self):
        """Test 1: Conexión TCP básica"""
        self.print_header("TEST 1: CONEXIÓN TCP")

        success, msg = self.connect_tcp()
        self.print_test(
            "Conexión al servidor TCP",
            success,
            f"Puerto {TCP_PORT}" if success else msg,
        )

        return success

    def test_tcp_commands(self):
        """Test 2: Comandos TCP"""
        self.print_header("TEST 2: PROTOCOLO TCP - COMANDOS")

        # Test LOGIN exitoso
        response = self.send_tcp_command("LOGIN admin admin123")
        self.print_test(
            "LOGIN con credenciales válidas", response.startswith("OK LOGIN"), response
        )

        # Test LIST
        response = self.send_tcp_command("LIST")
        self.print_test(
            "LIST - Listar dispositivos",
            response.startswith("OK") and "luz_salon" in response,
            f"Respuesta: {response[:60]}...",
        )

        # Test STATUS
        response = self.send_tcp_command("STATUS luz_salon")
        self.print_test(
            "STATUS - Consultar estado de luz_salon",
            response.startswith("OK"),
            response,
        )

        # Test SET ON
        response = self.send_tcp_command("SET luz_salon ON")
        self.print_test("SET - Encender luz_salon", "OK SET" in response, response)

        time.sleep(0.5)

        # Test SET OFF
        response = self.send_tcp_command("SET luz_salon OFF")
        self.print_test("SET - Apagar luz_salon", "OK SET" in response, response)

        # Test AUTO_OFF
        response = self.send_tcp_command("AUTO_OFF luz_salon 5")
        self.print_test(
            "AUTO_OFF - Programar autoapagado (5s)", "OK AUTO_OFF" in response, response
        )

        # Test LOG
        response = self.send_tcp_command("LOG")
        self.print_test(
            "LOG - Obtener historial",
            "OK LOG" in response,
            f"{len(response.split(chr(10)))} líneas de log",
        )

    def test_tcp_authentication(self):
        """Test 3: Autenticación"""
        self.print_header("TEST 3: AUTENTICACIÓN")

        # Crear nueva conexión sin login
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        test_socket.connect((TCP_HOST, TCP_PORT))
        test_socket.recv(4096)  # Leer bienvenida

        # Intentar SET sin login
        test_socket.send(b"SET luz_salon ON\n")
        response = test_socket.recv(4096).decode("utf-8").strip()

        self.print_test(
            "SET sin autenticación debe fallar",
            "ERROR" in response and "autenticación" in response.lower(),
            response,
        )

        # Login con credenciales incorrectas
        test_socket.send(b"LOGIN admin wrong_password\n")
        response = test_socket.recv(4096).decode("utf-8").strip()

        self.print_test(
            "LOGIN con contraseña incorrecta debe fallar", "ERROR" in response, response
        )

        test_socket.close()

    def test_api_endpoints(self):
        """Test 4: API REST"""
        self.print_header("TEST 4: API REST - ENDPOINTS")

        try:
            # Test GET /api/status
            response = requests.get(f"{API_BASE}/status", timeout=5)
            data = response.json()

            self.print_test(
                "GET /api/status",
                response.status_code == 200 and data.get("success"),
                f"{len(data.get('devices', []))} dispositivos encontrados",
            )

            # Test POST /api/control - Encender
            response = requests.post(
                f"{API_BASE}/control",
                json={"id": "enchufe_tv", "action": "ON"},
                timeout=5,
            )
            data = response.json()

            self.print_test(
                "POST /api/control - Encender enchufe_tv",
                response.status_code == 200 and data.get("success"),
                f"Estado: {data.get('new_state', 'N/A')}",
            )

            time.sleep(0.5)

            # Test POST /api/control - Apagar
            response = requests.post(
                f"{API_BASE}/control",
                json={"id": "enchufe_tv", "action": "OFF"},
                timeout=5,
            )
            data = response.json()

            self.print_test(
                "POST /api/control - Apagar enchufe_tv",
                response.status_code == 200 and data.get("success"),
                f"Estado: {data.get('new_state', 'N/A')}",
            )

            # Test POST /api/auto_off
            response = requests.post(
                f"{API_BASE}/auto_off",
                json={"id": "luz_salon", "seconds": 10},
                timeout=5,
            )
            data = response.json()

            self.print_test(
                "POST /api/auto_off - Programar autoapagado",
                response.status_code == 200 and data.get("success"),
                "10 segundos configurados",
            )

            # Test GET /api/log
            response = requests.get(f"{API_BASE}/log?limit=10", timeout=5)
            data = response.json()

            self.print_test(
                "GET /api/log",
                response.status_code == 200 and data.get("success"),
                f"{data.get('count', 0)} eventos en log",
            )

        except requests.exceptions.RequestException as e:
            self.print_test("API REST disponible", False, str(e))

    def test_auto_off_functionality(self):
        """Test 5: Funcionalidad de autoapagado"""
        self.print_header("TEST 5: AUTOAPAGADO AUTOMÁTICO")

        print(f"{YELLOW}ℹ️  Este test toma 6+ segundos...{RESET}\n")

        # Encender dispositivo
        self.send_tcp_command("SET enchufe_calefactor ON")
        time.sleep(0.5)

        # Verificar que está encendido
        response = self.send_tcp_command("STATUS enchufe_calefactor")
        initial_on = "ON" in response

        self.print_test("Dispositivo encendido inicialmente", initial_on, response)

        # Programar autoapagado de 5 segundos
        self.send_tcp_command("AUTO_OFF enchufe_calefactor 5")
        print(f"{YELLOW}⏳ Esperando 6 segundos para autoapagado...{RESET}")
        time.sleep(6)

        # Verificar que se apagó
        response = self.send_tcp_command("STATUS enchufe_calefactor")
        auto_off_worked = "OFF" in response

        self.print_test(
            "Dispositivo se apagó automáticamente tras 5s", auto_off_worked, response
        )

    def test_concurrent_operations(self):
        """Test 6: Operaciones concurrentes"""
        self.print_header("TEST 6: CONCURRENCIA")

        try:
            # Realizar múltiples operaciones simultáneas vía API
            import threading

            results = []

            def api_call():
                try:
                    r = requests.get(f"{API_BASE}/status", timeout=5)
                    results.append(r.status_code == 200)
                except Exception:
                    results.append(False)

            threads = [threading.Thread(target=api_call) for _ in range(5)]

            for t in threads:
                t.start()

            for t in threads:
                t.join()

            self.print_test(
                "5 llamadas API concurrentes",
                all(results),
                f"{sum(results)}/5 exitosas",
            )

        except Exception as e:
            self.print_test("Prueba de concurrencia", False, str(e))

    def cleanup(self):
        """Limpia recursos"""
        if self.tcp_socket:
            try:
                self.send_tcp_command("EXIT")
                self.tcp_socket.close()
            except Exception:
                pass

    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{BLUE}{'SISTEMA DOMÓTICO - SUITE DE PRUEBAS'.center(70)}{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}")
        print(f"\n{YELLOW}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{YELLOW}Servidor: {TCP_HOST}:{TCP_PORT}{RESET}\n")

        # Ejecutar tests
        if not self.test_tcp_connection():
            print(f"\n{RED}❌ No se pudo conectar al servidor.{RESET}")
            print(f"{YELLOW}Asegúrate de ejecutar: python server_domotico.py{RESET}\n")
            return

        self.test_tcp_commands()
        self.test_tcp_authentication()
        self.test_api_endpoints()
        self.test_auto_off_functionality()
        self.test_concurrent_operations()

        # Limpieza
        self.cleanup()

        # Resumen
        self.print_header("RESUMEN DE PRUEBAS")

        total = self.tests_passed + self.tests_failed
        percentage = (self.tests_passed / total * 100) if total > 0 else 0

        print(f"Total de pruebas:  {total}")
        print(f"{GREEN}Exitosas:          {self.tests_passed}{RESET}")
        print(f"{RED}Fallidas:          {self.tests_failed}{RESET}")
        print(f"Porcentaje éxito:  {percentage:.1f}%\n")

        if self.tests_failed == 0:
            print(f"{GREEN}{'=' * 70}{RESET}")
            print(
                f"{GREEN}{'✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE ✅'.center(70)}{RESET}"
            )
            print(f"{GREEN}{'=' * 70}{RESET}\n")
        else:
            print(f"{RED}{'=' * 70}{RESET}")
            print(f"{RED}{'⚠️  ALGUNAS PRUEBAS FALLARON ⚠️'.center(70)}{RESET}")
            print(f"{RED}{'=' * 70}{RESET}\n")


if __name__ == "__main__":
    runner = TestRunner()

    try:
        runner.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠️  Pruebas interrumpidas por el usuario{RESET}\n")
        runner.cleanup()
    except Exception as e:
        print(f"\n{RED}❌ Error inesperado: {e}{RESET}\n")
        runner.cleanup()
