import argparse
from omnibus import OmnibusCommunicator
from server import app, socketio, start_relay_sender

def main():
    parser = argparse.ArgumentParser(description="WebSocket server for Omnibus bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6767, help="Port to listen on (default: 6767)")
    parser.add_argument("--omnibus-host", default="localhost", help="Omnibus server host (default: localhost)")
    args = parser.parse_args()
    OmnibusCommunicator(args.omnibus_host)
    start_relay_sender()
    print(f">>> Starting SocketIO server on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
