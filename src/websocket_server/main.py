import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="WebSocket server for Omnibus bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6767, help="Port to listen on (default: 6767)")
    parser.add_argument("--workers", type=int, default=1, help="Gunicorn worker count (default: 1)")
    parser.add_argument("--threads", type=int, default=1, help="Gunicorn thread count for gthread worker (default: 1)")
    args = parser.parse_args()

    bind = f"{args.host}:{args.port}"
    target = "websocket_server.wsgi:application"
    print(
        f">>> Starting Gunicorn SocketIO server on {bind} "
        f"(workers={args.workers}, threads={args.threads})"
    )
    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "--worker-class",
            "gthread",
            "--workers",
            str(args.workers),
            "--threads",
            str(args.threads),
            "--bind",
            bind,
            target,
        ],
    )

if __name__ == "__main__":
    main()
