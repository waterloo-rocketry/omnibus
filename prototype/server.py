import zmq

context = zmq.Context()

frontend = context.socket(zmq.SUB)
frontend.bind("tcp://*:5559") # Publishers can connect to us on port 5559
frontend.setsockopt(zmq.SUBSCRIBE, b"") # Subscribe to all messages
backend = context.socket(zmq.PUB)
backend.bind("tcp://*:5560") # Subscribers can connect to us on port 5560

# Forward all traffic between publishers and subscribers
zmq.proxy(frontend, backend)
