import zmq

import tornado.ioloop
import tornado.web
import zmq.asyncio
import msgpack

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

async def zmq_subscriber():
    # Connect to ZMQ publisher
    context = zmq.asyncio.Context()

    socket = context.socket(zmq.SUB)
    socket.connect("tcp://127.0.0.1:5076")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')

    # Print broadcasted messages
    while True:
        channel, timestamp, payload = await socket.recv_multipart()
        print(channel.decode("utf-8"), msgpack.unpackb(timestamp), msgpack.unpackb(payload))

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    io_loop = tornado.ioloop.IOLoop.current()

    zmq_loop = zmq.asyncio.ZMQEventLoop()
    io_loop.asyncio_loop = zmq_loop

    io_loop.add_callback(zmq_subscriber)
    io_loop.start()