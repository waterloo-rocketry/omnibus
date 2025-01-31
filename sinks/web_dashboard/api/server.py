import zmq

import tornado.ioloop
import tornado.web
import zmq.asyncio

from omnibus import Receiver

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

async def zmq_subscriber():
    
    receiver = Receiver("")

    while True:
        data = receiver.recv()
        print(data)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    io_loop = tornado.ioloop.IOLoop.current()

    io_loop.add_callback(zmq_subscriber)
    io_loop.start()