import os
import simplejson
import event
from orbited import plugin
from orbited.log import getLogger
from orbited.orbit import FakeOPRequest
from orbited.config import map as config
from graph import Graph

logger = getLogger("Graph")

class GraphServer(plugin.Plugin):
    name = 'graph'
    static = os.path.join(os.path.split(__file__)[0], 'static')
    def __init__(self):
        self.connections = {}
        options = config.get('[graph]', {})
        filename = options.get('filename', 'benchmark.out')
        self.graph = Graph(filename)
        self.timer = None
        

    @plugin.dynamic
    def test(self,request,response):
        response.write('test!')

    @plugin.dynamic
    def join(self,request,response):
        response.write('%s has joined' % request.form.get('user',None))

    @plugin.hook("<transport.create")
    def orbited_connect(self, conn):
        if conn.key[2] == "/_/%s/event" % self.name:
            if not self.connections:
                self.graph.reset()
                self.timer = event.timeout(1,self.send)
            self.connections[conn.key] = conn
            logger.info("orbited connect!")
        
    @plugin.hook(">app.Application.remove_session")
    def orbited_disconnect(self, app, conn):
        if conn.key[2] == "/_/%s/event" % self.name:
            del self.connections[conn.key]
            logger.info("orbited d/c!")

    def send(self):
        data = simplejson.dumps(self.graph.update())
        if not self.connections:
            self.timer = None
            return None
        for player in self.connections.values():
            r = FakeOPRequest(data)
            player.event(r)
        return True
