import os
import event
from orbited import plugin
from orbited.log import getLogger
from orbited.orbit import FakeOPRequest

logger = getLogger("PSPlugin")

class PSPlugin(plugin.Plugin):
    name = "psplugin"
    static = os.path.join(os.path.split(__file__)[0], 'static')

    def __init__(self):
        self.connections = {}

    @plugin.hook("<transport.create")
    def orbited_connect(self, conn):
        if conn.key[2] in self.connections:
            self.connections[conn.key[2]].append(conn)
        else:
            self.connections[conn.key[2]] = [conn]
            logger.info('Location added: %s' % conn.key[2])
        
    @plugin.hook(">app.Application.remove_session")
    def orbited_disconnect(self, app, conn):
        self.connections[conn.key[2]].remove(conn)
        if not self.connections[conn.key[2]]:
            del self.connections[conn.key[2]]
            logger.info('Location removed: %s' % conn.key[2])

    @plugin.dynamic
    def send(self,request,response):
        loc = request.form['loc']
        msg = request.form['msg']
        logger.info('sending %s to %s' % (msg, loc))
        if loc in self.connections:
            for player in self.connections[loc]:
                r = FakeOPRequest(msg)
                player.event(r)
        response.write('SEND')
