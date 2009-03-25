from twisted.web import resource, error
from orbited.config import map as config
from orbited import logging

class TestResource(resource.Resource):
    def render(self, request):
        response = "<h2>Orbited.system.test</h2>"
        response += "stompdispatcher.enabled = "+config['[test]']['stompdispatcher.enabled']
        response += "<br><br>&lt; <a href='/system'>Orbited.system</a>"
        return response

    def getChild(self, path, request):
        if path.startswith('stomp'):
            return StompDispatcherResource()
        else:
            return error.NoResource()

class StompDispatcherResource(resource.Resource):
    logger = logging.get_logger('orbited.system.test.stompdispatcher')
    def render(self, request):
        self.logger.info("request received")
        if config['[test]']['stompdispatcher.enabled'] == '1':
            destination = request.args['dest'][0]
            message = request.args['msg'][0]
            self.logger.info("sending %s to %s"%(message, destination))
            config['morbid_instance'].send(destination, message)
        else:
            self.logger.info("stompdispatcher not enabled - message not dispatched")
            return "alert('stompdispatcher not enabled');"