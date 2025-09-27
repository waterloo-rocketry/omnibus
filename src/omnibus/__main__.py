from .server import server

try:
    server()
except KeyboardInterrupt:
    pass  # Should exit silently
