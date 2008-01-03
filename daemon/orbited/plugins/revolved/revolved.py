from replication.daemon import ReplicationDaemon
from orbited.log import getLogger
logger = getLogger("RevolvedServer")

class RevolvedServer(object):
    def __init__(self, orbited):
        self.users = {}
        self.channels = {}        
        self.orbited = orbited
        self.replication = ReplicationDaemon(self)

    def send(self, user_key, payload):
        pass

    def publish(self, channel, sender, payload, token=None, replicated=False):    
        logger.debug(str(sender) + " || " + channel + " || " + payload)
        if replicated:
            sender_key = sender
        else:
            sender_key = sender[0], sender[2]
            self.replication.publish(channel, sender_key, payload)
        if channel not in self.channels:
            return
        for user in self.channels[channel]:
            self.orbited.send(user, ('publish', channel, sender_key, payload))

    def subscribe(self, user_key, channel, token):
        if channel in self.users[user_key]:
            return
        self.users[user_key].append(channel)
        if channel not in self.channels:
            self.channels[channel] = []
        self.channels[channel].append(user_key)

    def unsubscribe(self, user_key, channel):
        if channel not in self.users[user_key]:
            return

        self.users[user_key].remove(channel)
        self.channels[channel].remove(user_key)

    def disconnect(self, user_key):
        for channel in self.users[user_key]:
            self.channels[channel].remove(user_key)
        del self.users[user_key]

    def connect(self, user_key):
        self.users[user_key] = []

    def move(self, old_key, new_key):
        self.users[new_key] = []
        for channel in self.users[old_key]:
            self.channels[channel].remove(old_key)
            self.channels[channel].append(new_key)
            self.users[new_key].append(channel)
        del self.users[old_key]
