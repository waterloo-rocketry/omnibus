import argparse
from relay import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Omnibus bridge relay")
    parser.add_argument("--host", default="127.0.0.1", help="WebSocket server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6767, help="WebSocket server port (default: 6767)")
    args = parser.parse_args()
    main(ws_url=f"http://{args.host}:{args.port}")
