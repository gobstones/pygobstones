import commons.concurrent as concurrent

class Message:
    def __init__(self, header, body = None):
        self.header = header
        self.body = body
        
class MessageCommunicator: 
    def __init__(self, queue_in=concurrent.Queue(), queue_out=concurrent.Queue()):
        self.queue_in = queue_in
        self.queue_out = queue_out
    def send(self, header, body=None):
        self.queue_out.put(Message(header, body))
    def receive(self):
        return self.queue_in.get()        
    def receive_nowait(self):
        return self.queue_in.get_nowait()
    def opposite(self):
        return MessageCommunicator(self.queue_out, self.queue_in)