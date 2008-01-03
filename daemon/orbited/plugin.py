import random
import logging
import pkg_resources
import orbited
from orbited.orbit import InternalOPRequest
from orbited.config import map as config
from orbited.json import json
from orbited.log import getLogger
from orbited.http.router import router
from orbited.util import formatBlock
from orbited.http.content import HTTPClose, HTTPContent, HTTPRequestComplete
import event

def randomkey():
    return "".join([random.choice("1234567890ABCDEFG") for i in range(6) ])

class Loader(object):
    logger = getLogger("Plugins")
    # logger.setLevel(logging.DEBUG)
    
    def __init__(self):
        self.plugins = {}
        self.hooks = {}
        self.active_hooks = {}
        self.hook_functions = {}
        router.register_plugin_loader(self)
    
    def attach_hook(self, plugin, target, source_name, direction):
        if source_name not in self.hooks:
            self.hooks[source_name] = {
                '>': [],
                '<': []
            }
        try:
            self.hooks[source_name][direction].append((plugin, getattr(plugin, target)))
        except AttributeError:
            self.logger.critical("Plugin %s: has no attribute: %s" % (plugin, target))
        except KeyError:
            self.logger.critical("Plugin %s: Invalid direction '%s'" % (plugin, direction))
            raise

    def start_plugin(self, plugin):
        self.logger.info("Starting Plugin: %s" % plugin.name)
        router.start_plugin(plugin)
        for source, target in plugin.hooks.items():
            direction = source[0]
            source_name = source[1:]
            target_func = getattr(plugin, target)
            if (plugin, target_func) not in self.active_hooks[source_name][direction]:
                self.active_hooks[source_name][direction].append((plugin, target_func))


    def stop_plugin(self, plugin):
        self.logger.info("Stopping Plugin: %s" % plugin.name)
        router.stop_plugin(plugin)
        for source, target in plugin.hooks.items():
            direction = source[0]
            source_name = source[1:]
            target_func = getattr(plugin, target)
            if (plugin, target_func) in self.active_hooks[source_name][direction]:
                self.active_hooks[source_name][direction].remove((plugin,target_func))

    def load(self):
        for plugin_entry in pkg_resources.iter_entry_points('orbited.plugins'):
            self.logger.info("Loading plugin: %s" % plugin_entry)
            try:
                plugin = plugin_entry.load()
            except:
                self.logger.error("Couldn't load %s" % plugin_entry.name,exc_info=True)
                continue
            self.plugins[plugin.name] = plugin()

        for plugin in self.plugins.values():
            router.register_plugin(plugin)
            for source, target in plugin.hooks.items(): 
                source_name = source[1:]
                direction = source[0]
                self.attach_hook(plugin, target, source_name, direction)

        for name in self.hooks.keys():
            try:
                self.hook_functions[name] = self.load_target(name)
            except:
                self.logger.critical("Plugin: %s, Invalid Hook: %s" % (self.hooks[name], name))
                raise
        for name in self.hooks.keys():
            self.active_hooks[name] = { '>': [], '<': [] }
        for plugin in self.plugins.values():
            if plugin.active():
                self.start_plugin(plugin)



    def import_target(self, name):
        cur = orbited
        parent = None
        func = None
        pieces = name.split('.')
        for i in range(len(pieces)):
            prev = '.'.join(pieces[:i])
            piece = pieces[i]
            val = getattr(cur, piece, None)
            if val is None:
                prev = 'orbited.' + '.'.join(pieces[:i+1])
                
                __import__(prev)
                val = getattr(cur, piece)
            if i == len(pieces)-1:
                func = val
            if i == len(pieces)-2:
                parent = val
            cur = val
        return parent, func, pieces[-1]
    
    def load_target(self, name):
        # Get the function
        parent, orig_func, orig_name = self.import_target(name)
        def hook_wrapper(*args, **kwargs):
            for plugin, in_hook in self.active_hooks[name]['>']:
                try:
                    in_hook(*args, **kwargs)
                except Exception:
                    self.logger.error("an error occured in wrapping functional call",exc_info=True)
            data = orig_func(*args, **kwargs)
            for plugin, out_hook in self.active_hooks[name]['<']:
                try:
                    out_hook(data)
                except Exception:
                    self.logger.error("an error occured in wrapping functional call",exc_info=True)
            return data
        
        self.logger.debug("setting... was: " + str(getattr(parent, orig_name)))
        setattr(parent, orig_name, hook_wrapper)
        self.logger.debug("set.. is: " + str(getattr(parent, orig_name)))
    
    def hook_in(self, name, *args, **kwargs):
        pass
    
    def hook_out(self, name, *args, **kwargs):
        pass
    

loader = Loader()

def load():
    loader.load()


class PluginMeta(type):
    def __init__(cls, name, bases, dct):
        if name == "Plugin":
            return
        if 'name' not in dct:
            raise Exception("plugin must have a name.")
        name = dct['name']        
        cls.options = config.get('[plugin:%s]' % cls.name, {})
        if 'active' not in cls.options:
            cls.options['active'] = '0'
        cls._plugin_active = cls.options['active'] == '1'
        cls._plugin_event_path = '/_/%s/plugin' % name
        old__init__ = cls.__init__
        def __init__replacement(self):
            old__init__(self)
            self._manager = cls.Management(self)
            self._application_keys = []
            self._connections = {}
            self._connection_timeouts = {}
#            if 'event_path' not in self.__dict__:
 #               self.event_path = '/_/%s/event' % (self.name,)
            
        cls.__init__ = __init__replacement
        if 'routing' not in dct:
            routing = {
                'base': '/_/%s' % name,
                'ORBITED': [ '/event' ],
            }
            if 'static' in dct:
                routing['static'] = { 
                    '/static': dct['static']
                }
            cls.routing = routing
        dynamic = []
        hooks = {}
        inheritance_tree = [ c.__dict__ for c in bases ] + [ dct]
        for c in inheritance_tree:
            for key, val in c.items():
                if hasattr(val, 'dynamic') and val.dynamic == True:
                    dynamic.append(key)
                if hasattr(val, 'hook'):
                    hooks[val.hook] = key
                
        cls._dynamic = dynamic
        cls.hooks = hooks
    

def dynamic(func):
    func.dynamic = True    
    return func

def hook(target):
    def dec(func):
        func.hook = target
        return func
    
    return dec

class RawPlugin(object):
    pass


class RemoteManager(object):
    pass



def management(func):
    func._management = True
#    func.im_class._dir.append(func.im_func.func_name)
    return func

class Management(object):
    
    def __init__(self, plugin):
        self._dir = []
        self.plugin = plugin
        for name, value in self.__class__.__dict__.items():
            if hasattr(value, '_management'):
                self._dir.append(name)
        
    # Return a list of all supported functions
    @management
    def list(self,request, response):
        return response.write(json.encode([True, self._dir]))
    
    # Stop this plugin (if its running)
    @management
    def stop(self, request, response):
        if self.plugin._plugin_active:
            self.plugin._plugin_active = False
            loader.stop_plugin(self.plugin)
            self.plugin.stop()
            return response.write(json.encode([True, "success"]))
        return response.write(json.encode([False, "already stopped"]))
    
    # Start this plugin (if its not running)
    @management
    def start(self, request, response):
        if not self.plugin._plugin_active:
            self.plugin._plugin_active = True
            loader.start_plugin(self.plugin)
            self.plugin.start()
            return response.write(json.encode([True, "success"]))
        return response.write(json.encode([False, "already started"]))
    
    status_msg = { 
        True: "Plugin is running", 
        False: "Plugin is stopped"
    }
    
    @management
    def status(self, request, response):
        response.write(json.encode([True, self.status_msg[self.plugin._plugin_active]]))

    @management
    def name(self,request,response):
        response.write(json.encode([True, self.plugin.name]))
class Plugin(RawPlugin):
    __metaclass__ = PluginMeta
    
    Management = Management
    
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def active(self):
        return self._plugin_active
        
    def dispatch(self, request):
        loc = request.url[len(self.routing['base']):]
        if len(loc) > 0 and loc[0] == "/":
            loc = loc[1:]
            
        if loc.startswith('manage/'):
            loc = loc[7:] # case (base/manage -> "") handled as well
            if loc == "":
                request.respond(HTTPContent(router.static["/_/plugin_management.html"]))
                request.respond(HTTPClose())
                return
            target = getattr(self._manager, loc, None)
            if target:
                response = PluginHTTPResponse(request)
                should_render = target(request, response)
                if should_render != False:
                    return response.render()
                return
                # otherwise proceed to 404
            
        elif self._plugin_active: 
            
            if loc == "":
                target = self.routing['base'] + '/static/index.html'
                if target in router.static:
                    request.respond(HTTPContent(router.static[target]))
                    request.respond(HTTPClose())
                    return
                # index
            elif loc in self._dynamic:
                response = PluginHTTPResponse(request)
                should_render = getattr(self, loc)(request, response)
                if should_render != False:
                    return response.render()
                return
        # 404
        headers = formatBlock('''
                HTTP/1.x 404 Not Found
                Content-Length: %s
                Content-Type: text/html
                Server: Orbited 0.2.0
            ''') + '\r\n\r\n'
        body = "Requested resource was not found"
        request.respond(HTTPContent(headers % (len(body)) + body))
        request.respond(HTTPRequestComplete())

    # Default Hooks
    @hook("<session.create")
    def orbited_connect(self, conn):
        print "session.create hook",conn,conn.key
        if conn.key[2].startswith(self.event_path):
            if conn.key[1] not in self._application_keys:
                return conn.close()
            self._connection_timeouts[conn.key[1]].delete()
            del self._connection_timeouts[conn.key[1]]
            self._connections[conn.key] = conn
            print self._connections
        if hasattr(self, 'accept_orbited_connection'):
            self.accept_orbited_connection(conn)

    @hook(">app.Application.remove_session")
    def orbited_disconnect(self, app, conn):
        if conn.key[2].startswith(self._plugin_event_path):
#            print "deleting: %s\nfrom: %s" % (conn.key, self._connections)
            del self._connections[conn.key]
            self._application_keys.remove(conn.key[1])
        if hasattr(self, 'orbited_connection_closed'):
            self.orbited_connection_closed(app, conn)

    def accept_orbited_connection(self,conn):
        pass

    def close_orbited_connection(self,conn):
        pass

    @dynamic
    def connect(self, request, response):
        key = randomkey()
        while key in self._application_keys:
            key = randomkey()
        self._application_keys.append(key)
        self._connection_timeouts[key] = event.timeout(30,self.connection_timeout,key)
        response.write(json.encode(key))

    def connection_timeout(self,key):
        del self._connection_timeouts[key]
        self._application_keys.remove(key)
        return None

    def broadcast(self):
        r = InternalOPRequest('('+json.encode(self.data)+')')
        for user in self._connections.values():
            user.event(r)


class PluginHTTPResponse(object):
    
    def __init__(self, request):
        self.request = request
        self.headers = {}
        self.buffer = []
    
    def __setitem__(self, key, val):
        self.headers[key] = val
    
    def __getitem__(self, key):
        return self.headers[key]
    
    def write(self, data):
        self.buffer.append(data)
    
    def dispatch(self):
        plugin.dispatch(self.request, self)
        self.render()   
    
    def render(self):
        status = "HTTP/1.x 200 OK\r\n"
        self.headers['Content-length'] = str(sum([len(s) for s in self.buffer]))
        h = "\r\n".join(": ".join((k, v)) for (k, v) in self.headers.items())
        h += "\r\n\r\n"
        response = status + h + "".join(self.buffer)
        self.request.respond(HTTPContent(response))
        self.request.respond(HTTPRequestComplete())

