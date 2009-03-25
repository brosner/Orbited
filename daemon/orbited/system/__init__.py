from twisted.web import resource, error
from orbited import __version__ as version
import test, monitor

class SystemResource(resource.Resource):
    def render(self, request):
        response = "<h2>Orbited.system</h2>"
        response += "Orbited version: "+version
        response += "<br><br>&gt; <a href='/system/test'>Orbited.system.test</a>"
        response += "<br>&gt; <a href='/system/monitor'>Orbited.system.monitor</a>"
        return response

    def getChild(self, path, request):
        if path == "test":
            return test.TestResource()
        elif path == "monitor":
            return monitor.MonitorResource()
        else:
            return error.NoResource()