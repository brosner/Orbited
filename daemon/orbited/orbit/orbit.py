from orbited import io
from orbited.config import map as config
from orbited.log import getLogger
import event

access = getLogger('ACCESS')

class OPDaemon(object):
    ''' The Orbit protocol daemon.
        
        This object listens on the Orbit protocol port, and accepts
        connections from Orbit clients.
    '''
    logger = getLogger('OrbitedDaemon')
    def __init__(self, app):
        self.port = int(config['[global]']['op.port'])
        self.logger.info('Listening on port %s' % self.port)
        self.index = 0
        self.app = app
        self.sock = io.server_socket(self.port)
        self.listen = event.event(self.accept_connection, 
            handle=self.sock, evtype=event.EV_READ | event.EV_PERSIST)
        self.listen.add()
    
    def accept_connection(self, event_, sock, event_type, *arg):
        self.index+=1
        connection = OPConnection(sock.accept(), self.index, self)
    

class OPConnection(object):
    ''' An Orbit Protocol connection.
        
        One of these objects is created when a client connects to the daemon,
        and handles reading from and writing to the socket.
    '''
    logger = getLogger('OrbitedConnection')
    def __init__(self, (sock, addr), id, daemon):
        self.daemon = daemon
        self.logger.debug('Accepting Orbit Connection [id: %s ] from %s on port %s' % ((id,) + addr))
        access.info('ACCESS\tOP [id: %s]\t%s\t%s' % ((id,) + addr))
        self.id = id
        self.app = daemon.app
        self.addr = addr
        self.sock = sock
        self.revent = event.read(sock, self.read_data)
        self.wevent = None
        self.response_queue = []
        self.write_buffer = ''
        self.request = OPRequest(self)
    
    def close(self):
        self.logger.debug('Closing Orbit Connection [id: %s ] from %s on port %s' % ((self.id,) + self.addr))
        self.wevent = None
        self.revent = None
        self.sock.close()
    
    def read_data(self):
        try:
            data = self.sock.recv(io.BUFFER_SIZE)
        except:
            data = None
        if not data:
            self.close()
            return None
        try:
            self.request.read_data(data)
        except RequestComplete, ex:
            self.logger.debug('Request finished. Start a new one')
            self.app.dispatch_event(self.request)
            self.request = OPRequest(self, ex.leftover_buffer)   
            while True:
                try:
                    self.request.process()
                    break
                except RequestComplete, ex:
                    self.app.dispatch_event(self.request)
                    self.request = OPRequest(self, ex.leftover_buffer)
        return True
    
    def write_data(self):
        try:
            bsent = self.sock.send(self.write_buffer)
            self.logger.debug('wrote:\n======\n%s' % self.write_buffer[:bsent])
            self.write_buffer = self.write_buffer[bsent:]
            return self.write_next()
        except io.socket.error:
            return None
    
    def write_next(self):
        if not self.write_buffer:
            if not self.response_queue:
                self.wevent = None
                return None
            else:
                self.write_buffer = self.response_queue.pop(0)
                if not self.wevent:
                    self.wevent = event.write(self.sock, self.write_data)
                return True
    
    def respond(self, response):
        self.response_queue.append(response)
        self.write_next()
    

class RequestComplete(Exception):
    
    def __init__(self, leftover_buffer):
        self.leftover_buffer = leftover_buffer
        Exception.__init__(self)
    

class OPRequest(object):
    ''' An Orbit Protocol request object.
        
        One of these objects is created along with each connection, and deals
        with high-level aspects of the Orbited response.
    '''
    logger = getLogger('OrbitedRequest')
    def __init__(self, connection, buffer=''):
        self.connection = connection
        self.addr = self.connection.addr[0]
        self.version = None
        self.type = None
        self.id = None
        self.recipients = []
        self.replies = {}
        self.state = 'version'
        self.buffer = buffer
        
    def key(self):
        if not self.id:
            raise 'NoKey'        
        return self.connection.id, self.id
        
        
    def read_data(self, data):
#        print "read:\n=====\n %s" % data
        self.buffer += data
        self.process()
            
    def process(self):
        if self.state == 'body':
            if len(self.buffer) < self.length:
                return
            self.payload = self.buffer[:self.length]
            self.logger.debug('body: %s' % self.payload)
            self.buffer = self.buffer[self.length:]
            raise RequestComplete(self.buffer)
            
        if '\r\n' in self.buffer:
            i = self.buffer.find('\r\n')
            line = self.buffer[:i]
            self.buffer = self.buffer[i+2:]
            getattr(self, 'state_%s' % self.state)(line)
            self.process()
            
        
    def state_version(self, line):
        if not line.startswith('Orbit/'):
            self.logger.error('Expected ORBIT protocol request.  Got something else.')
            # TODO: bail out, and stop processing the request
        self.logger.debug('version: %s' % line)
        self.version = line
        self.state = 'type'
        
    def state_type(self, line):
        # TODO: figure out what kind of input type can be.  error on anything else.
        self.logger.debug('type: %s' % line)
        self.type = line
        self.state = 'headers'
        
    def state_headers(self, line):
        self.logger.debug('header: %s' % line)
        if line == '':
            self.state = 'body'
            return
        try:
            name, content = line.split(': ', 1)
            name = name.lower()
            if name == 'id':
                self.id = content
            elif name == 'recipient':
                self.recipients.append(tuple(content.split(', ')))
            elif name == 'length':
                self.length = int(content)
            else:
                self.logger.error('Unrecognized header name: "%s"' % name)
                # TODO: error: unrecognized header name.  maybe bail? or just ignore it?
        except ValueError:
            # this can happen if we have no ': ', or if length is not an int.
            self.logger.error('Malformed header line: %s' % line)
            # TODO: error: mal-formed header.  we should bail out here? or just ignore it?

    def failure(self, recipient_key):
        recipient = '(%s, %s, %s)' % recipient_key
        self.replies[recipient] = 0
        if len(self.replies.keys()) == len(self.recipients):
            self.reply()
    
    def success(self, recipient_key):
        recipient = '(%s, %s, %s)' % recipient_key
        self.replies[recipient] = 1
        if len(self.replies.keys()) == len(self.recipients):
            self.reply()
    
    def reply(self):
        if len(self.recipients) == sum(self.replies.values()):
            self.reply_success()
        else:
            self.reply_failure()
    
    def reply_success(self):
        response = 'Success\r\nid: %s\r\n\r\n' % self.id
        self.connection.respond(response)
        
    def reply_failure(self):
        response = 'Failure\r\nid: %s\r\nmsg: Failed to reach one or more recipients\r\n' % self.id
        for recipient, success in self.replies.items():
            if not success:
                response += 'recipient: %s\r\n' % (recipient,)
        response += '\r\n'
        self.connection.respond(response)
        
class InternalOPRequest(object):
    id = 0
    addr = 'INTERNAL'
    
    def __init__(self, payload, succ_cb=None, fail_cb=None):
        InternalOPRequest.id +=1 
        self.id = InternalOPRequest.id
        self.payload = payload
        self.succ_cb = succ_cb
        self.fail_cb = fail_cb
        
    def success(self, key):
        if self.succ_cb:
            self.succ_cb(self, key)
            
    def failure(self, key):
        if self.fail_cb:
            self.fail_cb(self, key)
#for compatibility with existing plugins
FakeOPRequest = InternalOPRequest
