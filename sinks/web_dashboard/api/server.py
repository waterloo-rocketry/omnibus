import tornado.ioloop
import tornado.web
import tornado.websocket

import json

from omnibus.omnibus import Receiver

receiver = Receiver("")
clients = set()

class WebSocket(tornado.websocket.WebSocketHandler):

    # To allow connections from all origins (CORS)
    def check_origin(self, origin):
        return True

    def open(self):
        clients.add(self)
        print("WebSocket connection opened.")

    def on_message(self, message):
        print("Received message from client:", message)

    def on_close(self):
        clients.remove(self)
        print("WebSocket connection closed.")

def make_app():
    return tornado.web.Application([
        (r"/ws", WebSocket),
    ])

def zmq_subscriber():
    data = receiver.recv_message(None)
    stringified_json = json.dumps(data.payload)

    if (data.channel == "DAQ/Fake"):
        
        for client in list(clients):
            try:
                client.write_message(stringified_json)
            except:
                clients.remove(client)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Tornado Server Up")
    tornado.ioloop.PeriodicCallback(zmq_subscriber, 50).start()
    tornado.ioloop.IOLoop.current().start()
