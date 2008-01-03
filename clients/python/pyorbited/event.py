import socket
import event
LQUEUE_SIZE = 500
BUFFER_SIZE = 4096

END = '\r\n\r\n'
LINE = '\r\n'

def cb(req):
    print req.status
    print req.headers
    event.abort()
    
def cb2(req):
    print req.status
    print req.headers

def client_socket(addr, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    sock.connect_ex((addr, port))
    return sock    

def jsonify(self, data):
    return data
    
class Client(object):
    def __init__(self, servers, jscript=None):        
        if jscript:
            self.jscript = jscript
        self.servers = servers
        self.connections = dict()
        self.connections[0] = Connection(0, "localhost", 9000)
        self.connections[1] = Connection(1, "localhost", 9000)
        self.id = 0
#    def connect_all(self):
#        for connection in self.connections.values():
#            connection.connect()
        
    def event(self, recipients, data, callback=None, jscript=True, timeout=10):
        self.id += 1
        if jscript:
            data = jsonify(data)
        r = Request(self, self.id, recipients, data, callback)
        if not callback:
            # this timeout isn't good for real use. just so the interpreter
            # doesn't hang while testing.
            tevent = event.timeout(timeout, event.abort)
            event.dispatch()
            tevent.delete()
            return r
            
    def get_conn(self, id):
        return self.connections[id]
            
    def hash(self, key):
        if 'carn' in key:
            return 0
        return 1


class Request(object):
    def __init__(self, client, id, recipients, data, callback=None):
        self.id = id
        self.callback = callback
        self.replies = dict()
        self.requests = dict()
        self.data = data
        for recipient in recipients:
            num = client.hash(recipient)
            if num not in self.requests:
                self.requests[num] = []
            self.requests[num].append(recipient)
            
        for server_id in self.requests.keys():
            client.get_conn(server_id).event(self)
        


    def render(self, connection):
        out  = "Orbit 1.0\r\nEvent\r\nid: %s\r\n" % self.id
        for recipient in self.requests[connection.id]:
            out += "recipient: %s\r\n" % recipient
        out += "length: %s\r\n\r\n" % len(self.data)
        out += self.data
#        print "request: %s" % out
        return out
        
    def reply(self, connection, status, headers):
        self.replies[connection.id] = status, headers
        if len(self.replies.keys()) == len(self.requests.keys()):
            self.complete()
            
    def complete(self):
        final_headers = {
            'msg': 'success',
            'id': self.id,
            'recipients': []
        }
        self.status = 'success'
        for status, headers in self.replies.values():
            if status.lower() == 'failure':
                self.status = 'failure'
                final_headers['msg'] = headers['msg']
                final_headers['recipients'].extend(headers['recipient'])
                
        self.headers = final_headers
        if self.status == 'success':
            del self.headers['recipients']
        # We are in synchronous mode...
        if not self.callback:
            return event.abort()
        # We are in asynchronous mode...
        self.callback(self)
        
class Connection(object):
    def __init__(self, id, addr, port):
        self.id = id
        self.sock = client_socket(addr, port)
        self.write_buffer = ""
        self.read_buffer = ""
        self.events = []
        self.pending_events = {}
        self.state = None
        self.revent = None
        self.wevent = None
        
    def close(self):
        pass
        
    def event(self, event):
        self.events.append(event)
        self.start_write()
        self.start_read()
            
    def start_write(self):
        if not self.wevent:
            self.next_event()
            self.wevent = event.write(self.sock, self.write_ready)
            
    def start_read(self):
        if not self.revent:
            self.revent = event.read(self.sock, self.read_ready)
            self.revent.add()
        
    def next_event(self):
        e = self.events.pop(0)
        self.pending_events[e.id] = e
        self.write_buffer = e.render(self)      
        
    def write_ready(self):
        bsent = self.sock.send(self.write_buffer)
#        print "=====wrote=====\n %s" % self.write_buffer[:bsent]
        self.write_buffer = self.write_buffer[bsent:]
        if not self.write_buffer:
            if not self.events:
#                print "Wrote ALL Events"
                self.wevent = None
                return None
            self.next_event()
        return True
        
    def read_ready(self):
        data = self.sock.recv(BUFFER_SIZE)
#        print "READ: %s" % data
        if not data:
            self.close()
            return None
        self.read_buffer += data
        if END in self.read_buffer:
            self.process()
#            self.state = None
#            self.start_write()
        return True   

    def process(self):
#        print "processing!"
        index = self.read_buffer.find(END)
        reply = self.read_buffer[:index]
        self.read_buffer = self.read_buffer[index+len(END):]
        lines = reply.split(LINE)
        status = lines[0]
        headers = {}
        for line in lines[1:]:
            key, val = line.split(': ')
            if key == 'recipient':
                if key in headers:
                    headers[key].append(val)# = [ headers[key], val ]
                else:
                    headers[key] = [val]
            else:
                headers[key] = val
#        print "FINISHED READ"
#        print "headers: %s" % headers
#        print "pending: %s" % self.pending_events
        event = self.pending_events.pop(int(headers['id']))
        event.reply(self, status, headers)
        