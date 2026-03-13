import argparse
from omnibus import Sender
from server import app, socketio

def main():
    parser = argparse.ArgumentParser(description="WebSocket server for Omnibus bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6767, help="Port to listen on (default: 6767)")
    args = parser.parse_args()
   
    _ = Sender() #Trigger auto discovery
    print(f">>> Starting SocketIO server on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
