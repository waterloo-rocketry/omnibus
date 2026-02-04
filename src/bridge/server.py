import time
import socketio
from omnibus import Receiver
from socketio import exceptions
import msgpack


def main():
    print("[bridge] Starting bridge relay loop...")

    # Connect to WebSocket server
    sio = socketio.Client(logger=False, engineio_logger=False)
    
    try:
        sio.connect("http://localhost:6767")
    except exceptions.ConnectionError:
        print(">>> Could not connect to WebSocket server at http://localhost:6767")
        return
    
    # Subscribe to all Omnibus channels
    receiver = Receiver("")

    while True:
        msg = receiver.recv_message(0)

        if msg:
            # Filter out loop-back messages
            if msg.channel == "send_back":
                print(">>> Ignoring loop-back message on 'send_back' channel")
                print(msg)
                continue

            # Broadcast message to WebSocket clients
            # Format: msgpack([channel, [timestamp, payload]])
            message_data = [msg.channel, [msg.timestamp, msg.payload]]
            packed_message = msgpack.packb(message_data)
            
            # Emit msgpack-encoded binary to server
            sio.emit("omnibus_message", packed_message)

        time.sleep(0.01)

if __name__ == "__main__":
    main()
