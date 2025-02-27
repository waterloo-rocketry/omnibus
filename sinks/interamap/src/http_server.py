import os
import sys
import http.server
import socketserver
import socket
import threading
from src.config import HTTP_SERVER_PORT

def check_permissions(folder: str) -> bool:
    """Return True if the folder is readable, otherwise False."""
    return os.access(folder, os.R_OK)

def get_local_ip() -> str:
    """Attempt to get the local IP address by connecting to a public DNS server.
    Fallback to localhost if any error occurs."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Use Google's DNS server address; no data is actually sent.
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def get_share_url() -> str:
    """Return the share URL based on the local IP and the configured port."""
    return f"http://{get_local_ip()}:{HTTP_SERVER_PORT}"

class ThreadedHTTPServer:
    def __init__(self, shared_dir: str, port: int = HTTP_SERVER_PORT):
        self.shared_dir = shared_dir
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the HTTP server in a background thread."""
        handler = self._make_handler(self.shared_dir)
        self.server = socketserver.TCPServer(("", self.port), handler)
        print(f"Serving '{self.shared_dir}' on http://localhost:{self.port}")
        print(f"Access this server from other devices with your IP address (e.g., http://{get_local_ip()}:{self.port})")
        
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True  # Ensure the thread won't prevent program exit
        self.thread.start()
        print("HTTP server is running...")

    def stop(self):
        """Stop the HTTP server gracefully."""
        if self.server:
            print("Stopping HTTP server...")
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            print("HTTP server stopped.")
            self.server = None
            self.thread = None
        else:
            print("Server is not running.")

    def toggle(self):
        """Toggle the server state."""
        if self.server:
            self.stop()
        else:
            self.start()

    def get_status(self) -> bool:
        return self.server is not None

    @staticmethod
    def _make_handler(shared_dir: str):
        """Generate a request handler class that serves files from the shared directory."""
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=shared_dir, **kwargs)
        return CustomHandler

if __name__ == "__main__":
    # Simple argument parsing
    if len(sys.argv) != 2:
        print("Usage: python server.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        sys.exit(1)

    if not check_permissions(folder):
        print(f"Error: Insufficient permissions for folder {folder}.")
        sys.exit(1)

    # Initialize and start the server
    server_manager = ThreadedHTTPServer(folder)
    server_manager.start()

    # Interactive loop: type 'stop' or press Ctrl+C to terminate the server.
    try:
        while True:
            command = input("Enter 'stop' to stop the server: ").strip().lower()
            if command == "stop":
                break
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received.")

    server_manager.stop()
