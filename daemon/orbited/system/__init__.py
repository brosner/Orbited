from twisted.web import resource, error
from orbited import __version__ as version
import test

class SystemResource(resource.Resource):
    def render(self, request):
        response = "<h2>Orbited.system</h2>"
        response += "Orbited version: "+version
        return response

    def getChild(self, path, request):
        if path == "test":
            return test.TestResource()
        else:
            return error.NoResource()