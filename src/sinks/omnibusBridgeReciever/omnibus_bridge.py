from socketio import SimpleClient
from omnibus import Receiver

def main():
    with SimpleClient(logger=True, engineio_logger=True) as sio:
        sio.connect("http://127.0.0.1:5000")
        print(sio.sid)
        sio.emit('my message', {'foo': 'bar'})
        while True:
            pass


if __name__ == "__main__":
    main()
