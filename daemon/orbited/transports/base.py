from orbited import logging
from twisted.web import server, resource
from twisted.internet import defer, reactor
logger = logging.get_logger('orbited.transports.base.CometTransport')
class CometTransport(resource.Resource):
    HEARTBEAT_INTERVAL = 5

    def __init__(self, conn):
        self.conn = conn
        self.open = False
        self.closed = False

    def render(self, request):
        self.open = True
        self.packets = []
        self.request = request
        self.opened()
#        self.request.notifiyFinish().addCallback(self.finished)
        self.resetHeartbeat()
        self.closeDeferred = defer.Deferred()
        self.conn.transportOpened(self)
        return server.NOT_DONE_YET

    def resetHeartbeat(self):
        self.heartbeatTimer = reactor.callLater(self.HEARTBEAT_INTERVAL, self.doHeartbeat)

    def doHeartbeat(self):
        if self.closed:
            logger.debug("don't send hearbeat -- we should be closed", )
            raise Exception("show tb...")
        else:
            self.writeHeartbeat()
            self.resetHeartbeat()

    def sendPacket(self, name, id, data=None):
        if isinstance(id, int):
            id = str(id)
        if data:
            self.packets.append((id, name, data))
        else:
            self.packets.append((id, name))

    def flush(self):
        if self.packets:
            self.write(self.packets)
            self.packets = []
        if self.heartbeatTimer:
            self.heartbeatTimer.cancel()
            self.resetHeartbeat()

    # i don't think this is ever called...
    def finished(self, arg):
        logger.debug('finished: %s'%(arg,))
        self.request = None
        self.close()

    def onClose(self):
        logger.debug('onClose called')
        return self.closeDeferred

    def close(self):
        if self.closed:
            logger.debug('close called - already closed')
            return
        self.closed = True
        logger.debug('close ', repr(self))
        self.heartbeatTimer.cancel()
        self.heartbeatTimer = None
        self.open = False
        if self.request:
            logger.debug('calling finish')
            self.request.finish()
        self.request = None
        self.closeDeferred.callback(self)
        self.closeDeferred = None

    # Override these
    def write(self, packets):
        raise Exception("NotImplemented")

    def opened(self):
        raise Exception("NotImplemented")

    def writeHeartbeat(self):
        raise Exception("NotImplemented")