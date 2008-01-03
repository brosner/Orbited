from pyorbited import twistedorbit as orbit_client
import mimetypes
import os
from urllib import unquote
from util import expose
from irc import RelayFactory
from twisted.internet import reactor 

def refresh(statics, name):
    f = open(os.path.join('static', name))
    statics[name] = f.read()
    f.close()

class App(object):
    def __init__(self):        
        self.irc_connections = {}
        self.orbit = orbit_client.OrbitClient()
        # self.orbit.connect()
        self.statics = {}
        self.load_statics()
        
        # self.factory = RelayFactory(self)
    
    def load_statics(self):
        for name in [ i for i in os.listdir('static') if not i.startswith('.') ]:
            f = open(os.path.join('static', name))
            self.statics[name] = f.read()
            f.close()
    
    def dispatch(self, request):
        # return request.response.send()
        # if request.url == '/connect':
        #     return self.connect(request)
        if request.url.startswith('/static/'):
            return self.static(request)
        if hasattr(self, request.url[1:]):
            f = getattr(self, request.url[1:])
            if hasattr(f, 'exposed'):
                try:
                    return f(request)
                except Exception, e:
                    self.error(request, e, f)
                    raise
            else:
                return self.forbidden(request)
        else:
            return self.not_found(request)
    
    def static(self, request):
        name = request.url[8:]
        if name not in self.statics:
            return self.not_found(request)
        refresh(self.statics, name)
        request.response.add_header('Content-type', mimetypes.guess_type(name)[0])
        request.response.write(self.statics[name])
        request.response.send()
    
    def error(self, request, e, func):
        request.response.write("An error occured in <b>%s</b>: %s" % (func.func_name, e))
        request.response.send()
    
    def forbidden(self, request):
        request.response.write('FORBIDDEN')
        request.response.send()
    
    def not_found(self, request):
        request.response.write('FILE NOT FOUND')
        request.response.send()
    
    # not an http function
    
    def irc_quit(self, conn):
        del self.irc_connections[conn.nickname]
    
    def send_intro(self, user):
        user_key = '%s, 0, /livehelp' % user
        factory = RelayFactory(user,self,user_key)
        reactor.connectTCP("penux", 6667, factory)
        self.irc_connections[user] = factory
        # self.orbit.event([user_key], '<script>document.domain="meekle.com"</script>', False)
    
    #===================================================
    # Exposed Web Functions
    # These are called by ajax in the irc client 
    #===================================================
    
    def ping_reply(self, request):
        """
        Every so often our irc client sends a ping over orbit. This is how
        the web client responds to that ping.
        """
        user = request.form['user']
        if user not in self.irc_connections:
            #request.response.write('you are already connected/connecting')
            return request.response.send()
        irc = self.irc_connections[user].client
        irc.ping_reply()
        request.response.send()
    ping_reply.exposed = True
    
    def connect(self, request):
        # Create a new IRC connection
        # add it to dictionary user_name -> connection
        user = request.form['user']
        if user in self.irc_connections:
            request.response.write('you are already connected/connecting')
            return request.response.send()            
        reactor.callLater(1, self.send_intro, user)            
        request.response.write("connecting...")
        request.response.send()
    connect.exposed = True
    
    def join(self, request):
        user = request.form['user']
        channel = request.form['channel']
        key = request.form.get('key', None)
        irc = self.irc_connections[user].client
        irc.join(channel, key)
        request.response.write('<b>%s</b> joined <b>%s</b>' % (user, channel))
        request.response.send()
    join.exposed = True
    
    def quit(self, request):
        user = request.form['user']
        if user not in self.irc_connections:
            request.response.write('<b>%s</b> was not logged in' % user)
            request.response.send()
            return
        irc = self.irc_connections[user].client
        irc.quit("leaving livehelp")
        request.response.write('<b>%s</b> quit' % user)
        request.response.send()
    quit.exposed = True
    
    def changeNick(self, conn, nick):
        self.irc_connections[nick] = self.irc_connections.pop(conn.nickname)
    
    def nick(self, request):
        user = request.form['user']
        nick = request.form['nickname']
        irc = self.irc_connections[user].client
        irc.setNick(nick)
    nick.exposed = True
    
    def msg(self, request):    
        user = request.form['user']
        to = unquote(request.form['to'])
        msg = unquote(request.form['msg'])
        if user not in self.irc_connections: 
            request.response.write('User <b>%s</b> is not connected. Click <a href="/connect?user=%s">here</a> to connect.' % (user, user))
            return request.response.send()
        irc = self.irc_connections[user].client
        if msg.startswith("/"):
            if msg.startswith('/me '):
                irc.me(to, msg[4:])
                irc.action(user, to, msg[4:])
            else:
                command = msg.split(' ')[0]
                message = 'Livehelp does not support the %s command' % command
                irc.info_message(to, message)
        else:
            irc.msg(to, msg)
            irc.privmsg(user, to, msg)
        request.response.write('[%s] %s: %s' % (user, to, msg))
        request.response.send()
    msg.exposed = True
    

