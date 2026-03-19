import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="WebSocket server for Omnibus bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6767, help="Port to listen on (default: 6767)")
    args = parser.parse_args()

    bind = f"{args.host}:{args.port}"
    target = "websocket_server.wsgi:application"
    print(f">>> Starting Gunicorn SocketIO server on {bind}")
    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "--worker-class",
            "eventlet",
            "--workers",
            "1",
            "--bind",
            bind,
            target,
        ],
    )

if __name__ == "__main__":
    main()