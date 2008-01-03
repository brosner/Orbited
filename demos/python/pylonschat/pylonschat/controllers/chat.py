from pyorbited.simple import Client

import logging

from pylonschat.lib.base import *

log = logging.getLogger(__name__)

class ChatController(BaseController):

    orbit = Client()
    users = []
    
    def _user_keys(self):
        return ["%s, %s, /pylonschat" % (user[0], str(user[1]))
            for user in self.users]
    
    def index(self):
        return render('chat/index.html')

    def join(self, user, session='0'):
        if (user, session) not in self.users:
            self.users.append((user, session))
            self.orbit.event(self._user_keys(), '<b>%s joined</b>' % user)
        return "ok."
    
    def msg(self, user, msg, id=None, session='0'):
        self.orbit.event(self._user_keys(), '<b>%s</b> %s' % (user, msg))
        return "ok."
