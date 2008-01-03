import os
from orbited import plugin
from orbited.log import getLogger

logger = getLogger("SimplePlugin")

class SimplePlugin(plugin.Plugin):
    
    name = 'simple'
    static = os.path.join(os.path.split(__file__)[0], 'static')
    
    @plugin.dynamic
    def foo(self, request, response):
        response['Connection'] = 'keep-alive'
        response['keep-alive'] = '300'
        response.write("You called Foo!")
    
    @plugin.dynamic
    def bar(self, request, response):
        response.write("You called Bar!")
    
    # Hooks 
#    @plugin.hook("<transport.create")
#    def orbited_connect(self, conn):
#        logger.info("orbited connect!")
    
#    @plugin.hook(">app.Application.remove_session")
#    def orbited_disconnect(self, app, conn):
#        logger.info("orbited d/c!")
    

