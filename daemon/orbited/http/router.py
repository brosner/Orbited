import mimetypes
import os
import sys
from orbited.config import map as config
from orbited.log import getLogger
from orbited.util import formatBlock
logger = getLogger('Router')

class StaticDestination(object):
    def __init__(self, url, content):
        self.url = url
        self.content = content
    

class ProxyDestination(object):
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
    

#class NoDestination(object):
#    def __init__(self, error):
#        self.error = error
#    pass

class PluginDestination(object):
    def __init__(self, plugin, url):
        self.plugin = plugin
        self.url = url
    

class OrbitedDestination(object):
    pass

class OrbitedEventRequest(object):
    pass


class Router(object):
    def __init__(self):
        self.proxy_rules = config['[proxy]']        
        self.proxy_enabled = bool(int(config['[global]']['proxy.enabled']))
        self.prefixes = {}
        self.prefix_order = []
        self.static = {
            '/_/about': about,
        }
    
    def setup(self):
        sdir = os.path.join(os.path.split(__file__)[0], '..', 'static')
        self.register_static('/_/', sdir)    
        if self.proxy_enabled:
            for prefix, (addr, port) in self.proxy_rules:
                if addr == 'ORBITED':
                    self.register_orbited(prefix)
                else:
                    self.register_proxy(prefix, (addr, port))
        if '/' not in self.prefixes:
            self.register_orbited('/')
        logger.info('prefixes: %s' % (self.prefixes,))
        logger.info('prefix_order: %s' % (self.prefix_order,))
        # TODO: create a sorted list of router prefixes for efficient pattern matching.
    
    def register_plugin_loader(self, loader):
        self.plugin_loader = loader
    
    def stop_plugin(self, plugin):
        base = plugin.routing['base']
        to_remove = []
        for prefix in self.prefix_order:
            if prefix.startswith(base) and prefix != base:
                print "removing", prefix
                to_remove.append(prefix)#self.prefix_order.remove(prefix)
#                del self.prefixes[prefix]
            else:
                print "not removing", prefix
        
        for prefix in to_remove:
            self.prefix_order.remove(prefix)
            
    def start_plugin(self, plugin):
        base = plugin.routing['base']
        index = self.prefix_order.index(base)
        self.prefix_order.insert(index, base + '/event')
        self.prefix_order.insert(index, base + '/static/')


    def register_plugin(self, plugin):
#        if 'base' not in plugin.routing:
#            logger.warn('Plugin %s has no base url. It has not been registered with the router' % plugin.name)
        
#            return
#        index = None
#        if plugin.routing['base'] in self.prefix_order:
#            index = self.prefix_order.index(plugin.routing['base'])
        for prefix, dir in plugin.routing.get('static', {}).items():
            if prefix[-1] != '/':
                prefix = prefix + '/'
            full_prefix = plugin.routing['base'] + prefix
            print "register_static", full_prefix
            self.register_static(full_prefix, dir, order=False)            
        for prefix in plugin.routing.get('ORBITED', []):
            self.register_orbited(plugin.routing['base'] + prefix, order=False)
        self.prefixes[plugin.routing['base']] = ('plugin', plugin.name)
        self.prefix_order.append(plugin.routing['base'])
            
        # Put the catch at the end in case plugins are started and stopped while running
#        if '/' in self.prefix_order:
#            self.prefix_order.remove('/')
#            self.prefix_order.append('/')


    def register_orbited(self, prefix, order=True):
        self.prefixes[prefix] = ('orbited', None)
        if order:
            self.prefix_order.append(prefix)
    
    def register_static(self, prefix, root_dir, index=None, order=True):
        if prefix in self.prefixes:
            raise Exception('%s prefix refers to more than one route' % (prefix,))
        self.prefixes[prefix] = ('static', None)
        if order:
            self.prefix_order.append(prefix)
        root_len = len(root_dir)
        for dir, subdirs, files in os.walk(root_dir):
            for file in files:
                loc = os.path.join(dir, file)[root_len+1:].replace(os.path.sep, '/')
                url = prefix + loc
                
                if url in self.static:
                    raise Exception('%s refers to more than one resource' % url)
                f = open(os.path.join(dir, file), 'rb')
                data = f.read()
                f.close()
                output = formatBlock('''
                    HTTP/1.1 200 OK
                    Content-type: %s
                    Content-length: %s
                    
                    %s
                ''') % (mimetypes.guess_type(file)[0], len(data), data)
                self.static[url] = output
    
    def register_proxy(self, prefix, (addr, port), index=None, order=True):
        self.prefixes[prefix] = ("proxy", (addr, port))
        if order:
            self.prefix_order.append(prefix)
    
    def __call__(self, request):
        # TODO: use sorted prefix list for fast matching
        if request.url == '/favicon.ico':
            request.url = '/_/favicon.ico'        
        for prefix in self.prefix_order:
            (action, data)= self.prefixes[prefix]
            if request.url.startswith(prefix):
                if action == 'static':
                    if request.url in self.static:
                        return StaticDestination(request.url, self.static[request.url])
                if action == 'proxy':
                    addr, port = data
                    return ProxyDestination(addr, port)
                if action == 'orbited':
                    return OrbitedDestination()
                if action == 'plugin':
                    return PluginDestination(self.plugin_loader.plugins[data], request.url)
        raise Exception, '404'
        
        #if request.url == '/_/event':
        #    return OrbitedEventRequest()    
    

def setup():
    router.setup()

about = formatBlock('''
        HTTP/1.0 200 OK
        Content-Type: text/html
        
        <!DOCTYPE HTML>
        <html>
          <head>
            <meta charset="utf-8">
            <title>Orbited 0.2.0</title>
          </head>
          <body>
            <h1>Orbited 0.2.0</h1>
            <p>
              Python %s on %s
            </p>
          </body>
        </html>
    ''') % (sys.version.replace('\n', '<br>\r\n      '), sys.platform)
    
router = Router()
