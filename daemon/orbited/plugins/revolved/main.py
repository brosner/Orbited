import os
import pkg_resources
import random
import event
from orbited import plugin
from orbited.json import json
from orbited.log import getLogger
from orbited.orbit import InternalOPRequest
from revolved import RevolvedServer
logger = getLogger("Revolved")

Authenticator = None

class DefaultAuthenticator(object):
    # TODO: implement something that allows just guests or lurkers.
    #       and keeps guest names unique

    def __init__(self, revolved,  test=False):
        self.revolved = revolved
        self.test = test
        self.guests = []

    def connect(self, request, response):
        resource = request.form.get('resource', None)
        session = "".join([random.choice("1234567890ABCDEFG") for i in range(6) ])
        while session in self.revolved.sessions:
            session = "".join([random.choice("1234567890ABCDEFG") for i in range(6) ])
        return self.revolved.connect_response(request,response,value=(session, None, "lurk", None))

    def authenticate(self, request, response):
        user_name = request.form.get('userid', None)
        token = request.form.get('token', None)
        if token:
            conn_type = 'auth'
        else:
            conn_type = 'anon'
        session = request.form.get('session', None)
        if session not in self.revolved.sessions:
            error = ("InvalidSession", "Invalid session key")            
            return self.revolved.authenticate_response(request, response, error=error)# Fail
        if conn_type is not 'anon':
            error = ("OnlyAnonAllowed", "Only Anonymous access allowed")
            return self.revolved.authenticate_response(request, response, error=error)# Fail
        if user_name in self.guests:
            error = ("NAmeTaken", "That name is already taken")
            return self.revolved.authenticate_response(request, response, error=error)# Fail
#        self.guests.append(user_name)
        val = None, user_name, 'anon'
        return self.revolved.authenticate_response(request, response, value=val)

    def disconnect(self, session, user, conn_type, resource, app_key):
#        if user in self.guests:
#            self.guests.remove(user)
        return

def load_authenticator(revolved):
    global Authenticator
    authenticators = [ a for a in pkg_resources.iter_entry_points('revolved.authenticator') ]
    names = [a.name for a in authenticators ]
    if revolved.options.get('authenticator', None) not in names:
        print "using default Authenticator"
        Authenticator = DefaultAuthenticator
        return
    Authenticator = authenticators[names.index(revolved.options['authenticator'])].load()

class RevolvedPlugin(plugin.Plugin):
    name = 'revolved'
    event_path = "/_/revolved/event"
    static = os.path.join(os.path.split(__file__)[0], 'static')

    def __init__(self):
        if Authenticator is None:
            load_authenticator(self)
        self.revolved = RevolvedServer(self)
        self.sessions = {}
        self.connections = {}
        TEST = self.options.get('test', '0') == '1'
        self.authenticator = Authenticator(self,test=TEST)

#    @plugin.hook("<session.create")
    def accept_orbited_connection(self, conn):
        if conn.key[2].startswith(self.event_path):
            nothing, session, location = conn.key
            if session not in self.sessions:
                return conn.close()
            user, conn_type, resource, app_key = self.sessions[session]
            user_key = (session, resource)
            self.connections[user_key] = conn
            logger.info("Revolved connect! [ %s ] " % (conn.key,))

#    @plugin.hook(">app.Application.remove_session")
    def orbited_connection_closed(self, app, conn):
        logger.info("orbited d/c! [ %s ] " % (conn.key,))
        if conn.key[2].startswith(self.event_path):
            nothing, session, location = conn.key
            user, conn_type, resource, app_key = self.sessions[session]
            self.authenticator.disconnect(session, user, conn_type, resource, app_key)
            user_key = (session, resource)
            del self.connections[user_key]
            del self.sessions[session]
            logger.info("orbited d/c! [ %s ] " % (conn.key,))
            self.revolved.disconnect((user,session,resource))

    @plugin.dynamic
    def authenticate(self, request, response):
        response['Connection'] = 'Keep-Alive'
        response['Keep-Alive'] = 'timeout=30'
        self.authenticator.authenticate(request, response)
        return False

    def authenticate_response(self, request, response, value=None, error=None):
        if value:
            session = request.form.get('session', None)
            old_user, old_conn_type, resource, old_app_key = self.sessions[session]
            new_app_key, new_user, new_conn_type = value
            old_key = (old_user, session, resource)
            new_key = (new_user, session, resource)
            self.revolved.move(old_key, new_key)
            self.sessions[session] = new_user,new_conn_type,resource,new_app_key
            response.write(json.encode(("success")))
        elif error:
            response.write(json.encode(("failure", error[1])))
        else:
            response.write(json.encode(("failure", "auth malfunction")))
        response.render()

    @plugin.dynamic
    def connect(self, request, response):
        response['Connection'] = 'Keep-Alive'
        response['Keep-Alive'] = 'timeout=30'
        self.authenticator.connect(request, response)
        return False

    def connect_response(self, request, response, value=None, error=None):
      
        if value:
            session_id, user_name, conn_type, app_key = value
            resource = request.form.get('resource', None)
            self.sessions[session_id] = user_name, conn_type, resource, app_key
            # !!!
            # TODO: start timeout in case orbited.connect never happens
            # !!!
            self.revolved.connect((user_name,session_id,resource))
            response.write(json.encode(("success", session_id, user_name)))
        elif error:
            response.write(json.encode(("failure", error[1])))
        else:
            response.write(json.encode(("failure", "auth problem")))
        response.render()

    @plugin.dynamic
    def subscribe(self, request, response):
        response['Connection'] = 'Keep-Alive'
        response['Keep-Alive'] = 'timeout=30'
        status, d = self.pubsub_helper(request)
        if status == "success":
            user_key = (d['user'], d['session'], d['resource'])
            self.revolved.subscribe(user_key, d['channel'], d['channel_token'])
            return response.write("success")
        return response.write(status)

    @plugin.dynamic
    def unsubscribe(self, request, response):
        response['Connection'] = 'Keep-Alive'
        response['Keep-Alive'] = 'timeout=30'
        status, d = self.pubsub_helper(request)
        if status == "success":
            user_key = (d['user'], d['session'], d['resource'])
            self.revolved.unsubscribe(user_key, d['channel'])
            return response.write("success")
        return response.write(status)

    @plugin.dynamic
    def publish(self, request, response):
        response['Connection'] = 'Keep-Alive'
        response['Keep-Alive'] = 'timeout=30'
        # app-specific publish plugins
        status, d = self.pubsub_helper(request)
        if status == "success":
            user_key = (d['user'], d['session'], d['resource'])
            self.revolved.publish(d['channel'], user_key, d['payload'], d['channel_token'])
            return response.write("success")
        return response.write(status)

    def pubsub_helper(self, request):
        session = request.form.get('session', None)
        channel = request.form.get('channel', None)
        channel_token = request.form.get('token', None)
        payload = request.form.get('payload', None)
        if not channel:
            return "Specify channel",{}
        if not session:
            return "Specify session",{}
        user, conn_type, resource, app_key = self.sessions[session]
        if (session, resource) not in self.connections:
            return "Connection not found",{}
        return "success", {'session':session,'channel':channel,'channel_token':channel_token,'payload':payload,'user':user,'resource':resource}

    def send(self, revolved_key, payload ):
        payload = json.encode(payload)
        r = InternalOPRequest(payload)
        if revolved_key[1:] in self.connections:
            return self.connections[revolved_key[1:]].event(r)
        print "event delivery failure:",revolved_key[1:]
