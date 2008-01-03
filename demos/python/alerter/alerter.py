import cherrypy

class ChatServer(object):
    pass
    
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
