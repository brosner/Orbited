import event

from orbited import io
from content import HTTPContent
from orbited.config import map as config
from orbited.log import getLogger
from orbited.buffer import Buffer

   
class ProxyComplete(object):
    pass

class Proxy(object):
    logger = getLogger('proxy')
    # import logging; logger.setLevel(logging.DEBUG)
    id = 0
    def __init__(self, conn):
        Proxy.id += 1
        self.id = Proxy.id
        self.logger.debug('Creating Proxy with id %s' % self.id)
        self.conn = conn
        self.server = None
        self.state = 'waiting'
        self.keepalive = bool(int(config['[global]']['proxy.keepalive']))
        
        if self.conn.request.protocol == 'http/1.0':
            self.protocol = 1.0
            if self.keepalive:
                # Default for http/1.0 is to Close
                k = self.conn.request.headers.get('connection', 'Close')
                if k.lower() != 'keep-alive':
                    self.keepalive = False
        elif self.conn.request.protocol == 'http/1.1':
            self.protocol = 1.1
            if self.keepalive:
                # Default for http/1.1 is to Keep Alive
                k = self.conn.request.headers.get('connection', 'keep-alive')
                if k.lower() != 'keep-alive':
                    self.keepalive = False
        else:
            self.logger.debug('protocol is: %s' % self.conn.request.protocol)
            raise ProtocolError
    
    def proxy_request(self, addr, port):
        self.logger.debug('proxying request: %s, %s' % (addr, port))
        self.logger.debug('url: %s' % self.conn.request.url)
        if self.state != 'waiting':
            raise ProtocolError
        if self.server and self.server.location != (addr, port):
            self.logger.debug('old server is invalid')
            self.server.close()
            self.server = None
        if not self.server:
            self.logger.debug('creating new server')
            self.server = ServerConnection(self, addr, port)
        # TODO: possible improvement... don't copy the buffer, just pass it
        #       along and make a new buffer for the conn
        self.state = 'proxying'
        self.logger.debug('calling self.server.send_request')
        self.server.send_request(self.conn.buffer.get_value())        
    
    def completed(self):
        # TODO: check self.keepalive, and the server's connection header
        #       to figure out if we should close the server connection or not
        self.logger.debug('completed...')
        self.state = 'waiting'
    
    def close(self):
        if self.server:
            self.server.close()
            self.server = None
        self.state = 'closed'
    
    def relay_response(self, data):
        self.conn.write(data)
    
    def failure(self, err):
        self.logger.debug('proxy failed: %s ' % err)
        self.server.close()
        # TODO: check if we already started responding
        #       if we haven't, send an html error page
        #       if we have, then just close the connection entirely
        self.conn.close()
    

class ServerConnection(object):
    id = 0
    logger = getLogger('ServerConnection')
    # import logging; logger.setLevel(logging.DEBUG)    
    def __init__(self, proxy, addr, port):
        ServerConnection.id += 1
        self.id = ServerConnection.id
        self.logger.debug('CREATING ServerConnection with id %s' % self.id)
        self.proxy = proxy
        self.location = addr, port
        self.sock = io.client_socket(addr, port)
        self.revent = None #event.read(self.read_ready, self.sock)
        self.wevent = None
        self.write_buffer = None
        self.complete = False
        self.state = 'connecting'
    
    def send_request(self, data):
        self.logger.debug('entered send_request')
        if self.state == 'writing' or self.state == 'reading':
            raise ProtocolError
        
        self.buffer = ProxyBuffer()
        self.write_buffer = Buffer(data, mode='consume')
        self.wevent = event.write(self.sock, self.write_ready)
        self.logger.debug('exiting send_request')
    
    def read_ready(self):
        try:
            data = self.sock.recv(io.BUFFER_SIZE)
            self.buffer.recv(data)
            if self.buffer.out:
                content = HTTPContent(self.buffer.out.get_value())
                self.buffer.out.exhaust()
                self.proxy.relay_response(content)
            if self.buffer.complete:
                self.revent = None
                self.complete = True
                self.proxy.relay_response(HTTPContent(""))
                self.proxy.relay_response(ProxyComplete())
                self.state = 'waiting'
                return None
            return True
        except:
            raise
    
    def write_ready(self):
        self.logger.debug('entered write_ready')
        if self.state == 'connecting':
            self.state = 'writing'
        try:
            bsent = self.sock.send(self.write_buffer.get_value())
            self.write_buffer.move(bsent)
            if self.write_buffer.empty():
                self.logger.debug('Finished sending proxied request to server')
                self.wevent = None
                self.revent = event.read(self.sock, self.read_ready)
                self.state = 'reading'
                return None
        except io.socket.error, err:
            self.logger.debug('error')
            raise
            self.server_closed(err)
    
    def server_closed(self, err=None):
        if self.complete:
            pass
        else:
            self.proxy.failure(err)
    
    def close(self):
        if self.revent:
            self.revent.delete()
            self.revent = None
        if self.wevent:
            self.wevent.delete()
            self.wevent = None
        self.sock.close()
    

class ProxyBuffer(object):
    logger = getLogger('ProxyBuffer')
    def __init__(self):
        self.logger.debug('Creating new ProxyBuffer')
        self.buffer = Buffer()
        self.out = Buffer(mode='consume')
        self.mode = 'unknown'
        self.complete = False
        self.size_sent = 0
        self.state = 'status'
        self.headers = {}
        self.version = None
    
    def recv(self, data):
        if len(data) == 0 and self.version == 1.0:
            self.state = 'complete'
            return self.state_complete()            
        self.buffer += data
        return getattr(self, 'state_%s' % self.state)()
    
    # Inadequately named... more like "move_to_buffer"
    def send(self, i):
        self.out += self.buffer.part(0,i)
        self.buffer.move(i)
        self.size_sent += i
    
    def state_status(self):
        index = self.buffer.find('\r\n')
        if index == -1:
            return
        self.status = self.buffer.part(0,index)
        version_index = self.status.find(' ')
        version = self.status[:version_index]
        if version == 'HTTP/1.0':
            self.version = 1.0
        elif version == 'HTTP/1.1':
            self.version = 1.1
        else:
            raise 'InvalidHTTPVersion', version
        self.headers_length = len(self.status)+2
        self.send(index+2)
        self.state = 'headers'
        return self.state_headers()
    
    def state_headers(self):
        while True:
            index = self.buffer.find('\r\n')
            if index == -1:
                return
            header = self.buffer.part(0, index)
            self.send(index+2)
            self.headers_length += index + 2
            if index == 0:
                self.state = 'pre_body'
                return self.state_pre_body()
            key, val = header.split(': ')
            self.headers[key] = val
            if key == 'Content-Length':
                self.mode = 'normal'
                self.headers['Content-Length'] = int(self.headers['Content-Length'])
            if key == 'Transfer-Encoding' and val == 'chunked':
                self.mode = 'chunked'
    
    def state_pre_body(self):
        
        # HTTP/1.0
        if self.version == 1.0:
            self.state = 'http_1_0_body'
            return self.state_http_1_0_body()
        
        # HTTP/1.1 Implied 0 body length
        if self.mode == 'unknown':
            self.headers['Content-Length'] = 0
            self.state = 'complete'
            return self.state_complete()
        
        # HTTP/1.1 Chunked Transfer Encoding -- Annoying
        # TODO: implement this.
        if self.mode == 'chunked':
            raise ProtocolError, "'Transfer-Encoding: chunked' not supported"
            # self.state = 'chunked_body'
            # return self.chunked_body()            
        # HTTP/1.1 Standard request
        if self.mode == 'normal':
            self.state = 'body'
            self.size_left = self.headers['Content-Length']
            return self.state_body()
    
    def state_http_1_0_body(self):
        self.send(len(self.buffer))
    
    def state_body(self):
        index = len(self.buffer)
        if index > self.size_left:
            # Server sent us too much data...
            raise 'ExcessContentReceived'            
        self.send(index)
        self.size_left -= index
        if self.size_left == 0:
            self.state = 'complete'
            return self.state_complete()
    
    # def state_chunked_head(self):
    #     index = self.buffer.find('\r\n')
    #     if index == -1:
    #         return 
    #     chunk_head = self.buffer.part(0,index])
    #     self.out.append(self.buffer[:index+2])
    #     self.buffer = self.buffer[index+2:]
    #     size = int(chunk_head.split(';', 1)[0], 16)
    #     if size == 0:
    #         self.state == 'chunked_trailers'
    #         return self.state_chunked_trailers()
    # 
    # def state_chunked_body(self):
    #     index = self.buffer.find('\r\n')
    #     if index == -1:
    #         return 
    #     self.out.append(self.buffer[:index+2])
    #     self.buffer = self.buffer[index+2:]
    #     self.state_chunked_head()
    # 
    # def state_chunked_trailer(self):
    #     while True:
    #         index = self.buffer.find('\r\n')
    #         if index == -1:
    #             return 
    #         self.out += self.buffer[:index+2]
    #         self.buffer = self.buffer[2:]
    #         if index == 0:
    #             self.state = "complete"
    #             return self.state_complete()
    
    def state_complete(self):
        self.complete = True
        return
    
