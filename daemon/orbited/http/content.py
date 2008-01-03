from orbited.log import getLogger
logger = getLogger('HTTPContent')

class HTTPContent(object):
    id = 0    
    def __init__(self, content, succ_cb=None, fail_cb=None):
        HTTPContent.id += 1
        self.id = HTTPContent.id
        self._content = content
        self.succ_cb = succ_cb
        self.fail_cb = fail_cb
    
    def success(self, conn):
        logger.debug('Successfully sent content [id: %s]' % self.id)
        if self.succ_cb:
            self.succ_cb(conn)
    
    def failure(self, conn, reason):
        logger.debug('Failed to send content [id: %s], reason: %s' % (self.id, reason))
        if self.fail_cb:
            self.fail_cb(conn, reason)
    
    def content(self):
        return self._content
    

class HTTPClose(object):
    
    def success(self):
        pass
    
    def failed(self, reason):
        pass
    
    def content(self):
        return ''
    

class HTTPRequestComplete(object):
    
    def success(self):
        pass
    
    def failed(self, reason):
        pass
    
    def content(self):
        return ''
    
