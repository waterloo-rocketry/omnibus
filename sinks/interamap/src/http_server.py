import sys

import http.server
import socketserver
import socket

from config import HTTP_SERVER_PORT
import threading
import os

class ShareServer:
    def __init__(self, directory=os.getcwd() + "/sinks/interamap/shared", port=HTTP_SERVER_PORT):
        self.__httpd = None
        self.SHARED_DIR = directory
        self.PORT = port

    def start_map_folder_http_server(self):
        print(f"Starting HTTP server in folder '{self.SHARED_DIR}'")
        self.start_http_server_with_progress()

    def get_share_url(self):
        return f"http://{self.get_local_ip()}:{HTTP_SERVER_PORT}"

    def start_http_server_with_progress(self):

        server_thread = threading.Thread(target=lambda : self.start_http_server())
        server_thread.start()

        print("HTTP server is running...")


    def start_http_server(self):
        if self.__httpd is not None:
            print("Server already running.")
            return
        # Define the port to serve the HTTP server (default: 8000)
        shared_dir = self.SHARED_DIR
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=shared_dir, **kwargs)

        try:
            with socketserver.TCPServer(("", self.PORT), CustomHandler) as self.__httpd:
                print(f"Serving '{self.SHARED_DIR}' on http://localhost:{self.PORT}")
                print(f"Access this server from other devices with your IP address (e.g., http://{self.get_local_ip()}:{self.PORT})")
                print("Press Ctrl+C to stop the server.")
                # Start the server
                self.__httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

    def stop_http_server(self):
        if self.__httpd is not None:
            self.__httpd.shutdown()
            self.__httpd.server_close()
            self.__httpd = None
            print("HTTP server stopped.")
        else:
            print("No server running.")

    def server_running(self) -> bool:
        if self.__httpd is not None:
            return True
        else:
            return False

    @staticmethod
    def check_permissions(folder):
        # check if user has READ access
        if os.access(folder, os.R_OK):
            return True
        else:
            return False

    @staticmethod
    def get_local_ip():
        return socket.gethostbyname(socket.gethostname())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        sys.exit(1)

    server = ShareServer(folder)

    if not server.check_permissions(folder):
        print(f"Error: Insufficient permissions for folder {folder}.")
        sys.exit(1)

    server.start_http_server()
