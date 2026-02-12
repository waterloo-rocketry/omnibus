import time
import socketio
from omnibus import Receiver
from socketio import exceptions

def main():
    print("[bridge] Starting bridge relay loop...")

    # Connect to WebSocket server with native msgpack serialization
    sio = socketio.Client(logger=False, engineio_logger=False, serializer="msgpack")

    while True:
        try:
            sio.connect("http://127.0.0.1:6767")
            break
        except exceptions.ConnectionError:
            print(">>> Waiting for WebSocket server at http://127.0.0.1:6767...")
            time.sleep(1)

    # Subscribe to all Omnibus channels
    receiver = Receiver("")

    while True:
        msg = receiver.recv_message(0)

        if msg:
            # Filter out loop-back messages #IN ACRUAL NON TEST DO LOOP_BACK
            if msg.channel == "send_back":
                print(">>> Ignoring loop-back message on 'send_back' channel")
                print(msg)
                continue
        
            # serialized with msgpack by the socketio client
            sio.emit(msg.channel, [msg.timestamp, msg.payload])
            print("sent")

        time.sleep(0.01)

if __name__ == "__main__":
    main()
