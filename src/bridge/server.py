import time
import requests
from bridge.zmq_client import ZmqReceiver

# URL of the server2.py endpoint
SERVER2_URL = "http://localhost:8080/send-legacy-omnibus-information"

def main():
    receiver = ZmqReceiver()
    print("[bridge] Starting bridge relay loop...")
    while True:
        msg = receiver.receive(timeout_ms=100)
        if msg is not None:
            payload = {
                "channel": msg.channel,
                "timestamp": msg.timestamp,
                "payload": msg.payload,
            }
            try:
                r = requests.post(
                    SERVER2_URL,
                    json=payload,
                    timeout=1
                )
                print(f"[bridge] Sent to server2: {payload} | Response: {r.status_code}")
            except Exception as e:
                print(f"[bridge] Failed to send: {e}")
        time.sleep(0.01)

if __name__ == "__main__":
    main()
