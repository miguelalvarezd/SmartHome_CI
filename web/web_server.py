"""
Servidor Web para el Dashboard Domótico
Sirve el dashboard HTML y permite acceso desde otros dispositivos en la red.

Uso:
    python web/web_server.py [puerto]

Por defecto usa el puerto 8000.
Accesible en: http://<IP_DEL_SERVIDOR>:<PUERTO>/
"""

import http.server
import socketserver
import os
import sys
import socket

# Configuración
DEFAULT_PORT = 8000
WEB_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Handler personalizado para servir el dashboard."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIRECTORY, **kwargs)

    def do_GET(self):
        # Servir web_dashboard.html como página principal
        if self.path == "/" or self.path == "":
            self.path = "/web_dashboard.html"
        return super().do_GET()

    def log_message(self, format, *args):
        """Log personalizado con colores."""
        print(f"[WEB] {self.address_string()} - {args[0]}")


def get_local_ip():
    """Obtiene la IP local de la máquina."""
    try:
        # Crear un socket y conectar a una dirección externa
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    port = DEFAULT_PORT

    # Permitir especificar puerto por argumento
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Puerto inválido: {sys.argv[1]}")
            sys.exit(1)

    # Obtener IP local
    local_ip = get_local_ip()

    # Crear servidor
    with socketserver.TCPServer(("0.0.0.0", port), DashboardHandler) as httpd:
        print("=" * 60)
        print("   🏠 SERVIDOR WEB - DASHBOARD DOMÓTICO")
        print("=" * 60)
        print(f"\n📂 Sirviendo desde: {WEB_DIRECTORY}")
        print("\n🌐 Dashboard accesible en:")
        print(f"   • Local:    http://localhost:{port}/")
        print(f"   • Red:      http://{local_ip}:{port}/")
        print("\n⚠️  Asegúrate de que el servidor domótico está corriendo")
        print("    en el puerto 8080 para que el dashboard funcione.")
        print("\n🛑 Presiona Ctrl+C para detener el servidor")
        print("=" * 60 + "\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Servidor detenido.")
            sys.exit(0)


if __name__ == "__main__":
    main()
