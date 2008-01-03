import socket, io
from simplejson.encoder import JSONEncoder
encode = JSONEncoder().encode
END = '\r\n'

def debug(data):
    pass

class Client(object):
    version = 'Orbit 1.0'
    def __init__(self, addr="localhost", port=9000):
        self.addr = addr
        self.port = port
        self.socket = None
        self.id = 0
        self.connected = False
    
    def connect(self):
        self.connected = True
        if self.socket:
            debug("Already Connected")
            return
        self.socket = io.client_socket(self.addr, self.port)
        self.socket.setblocking(1)
    
    def disconnect(self):
        self.connected = False
        self.socket.close()
        self.socket = None
    
    def reconnect(self):
        self.disconnect()
        self.connect()
    
    def sendline(self, line=""):
        self.socket.send('%s%s' % (line, END))
    
    def event(self, recipients, body, json=True, retry=True):
        if not self.connected:
            self.connect()
        try:
            if json:
                body = encode(body)
            if not self.socket:
                raise IOError("ConnectionLost")
            try:
                self.id += 1
                self.sendline(self.version)
                self.sendline('Event')
                self.sendline('id: %s' % self.id)
                for recipient in recipients:
                    self.sendline('recipient: %s' % (str(recipient)))
                self.sendline('length: %s' % len(body))
                self.sendline()
                self.socket.send(body)
                return self.read_response()
            except socket.error:
                # self.disconnect()
                raise IOError("ConnectionLost")
        except IOError, e:
            if retry:
                self.reconnect()
                self.event(recipients, body, json, False)
            else:
                raise
    
    def read_response(self):
        return self.socket.recv(io.BUFFER_SIZE)
    
