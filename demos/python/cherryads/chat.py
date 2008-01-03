import cherrypy
from pyorbited.simple import Client
orbit = Client()

class ChatServer(object):
    users = []
    i = 0
    def user_keys(self):
        return ['%s, %s, /cherrychat' % (u, s) for u,s in self.users]
    
    @cherrypy.expose
    def join(self, user, session='0', id=None):
        if (user, session) not in self.users:
            self.users.append((user, session))
            orbit.event(self.user_keys(), '<b>%s joined</b>' % user)
    
    @cherrypy.expose
    def msg(self, user, msg,session='0', id=None):
        self.i += 1
        orbit.event(self.user_keys(), '<img width="599" height="81" src="/static/cool-ad%s.gif">' % ((self.i % 3) + 1 ))
        orbit.event(self.user_keys(), '<b>%s</b> %s' % (user, msg))

if __name__ == '__main__':
    import os
    # This code is straight from the cherrypy StaticContent wiki
    # which can be found here: http://www.cherrypy.org/wiki/StaticContent
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Set up site-wide config first so we get a log if errors occur.
    cherrypy.config.update({'environment': 'production',
                            'log.screen': True,
                            'server.socket_port': 4700,
                            'server.thread_pool': 0,
                            'tools.staticdir.root': current_dir})
        
    conf = {'/static': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': 'static'}}
    cherrypy.quickstart(ChatServer(), '/', config=conf)
