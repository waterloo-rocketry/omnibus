import os
import sys

import http.server
import socketserver
import socket

def check_permissions(folder):
    # check if user has READ access
    if os.access(folder, os.R_OK):
        return True
    else:
        return False

def get_local_ip():
    return socket.gethostbyname(socket.gethostname())


def start_http_server(SHARED_DIR):
    # Define the port to serve the HTTP server (default: 8000)
    PORT = 8000
     
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=SHARED_DIR, **kwargs)
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            print(f"Serving '{SHARED_DIR}' on http://localhost:{PORT}")
            print(f"Access this server from other devices with your IP address (e.g., http://{get_local_ip()}:{PORT})")
            print("Press Ctrl+C to stop the server.")
            # Start the server
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ftp_server.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        sys.exit(1)

    if not check_permissions(folder):
        print(f"Error: Insufficient permissions for folder {folder}.")
        sys.exit(1)

    start_http_server(folder)
