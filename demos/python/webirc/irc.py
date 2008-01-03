#import re
from twisted.internet import protocol, reactor
from twisted.words.protocols import irc
PING_INTERVAL = 100
PING_MISSED_MAX = 2

class RelayClient(irc.IRCClient):
    channel = '#orbited'
    def __init__(self, nickname, app, user_key):
        self.nickname = nickname
        self.orbit = app.orbit
        self.app = app
        self.user_key = user_key
        self.ping_count = 0
        self.name_reply = None

    def chan_names(self, channel, names, symbols='@%+'):
        # next line transforms unsorted list of names to list
        # sorted by rank-symbol (@, % or +), name
#        names = reduce(list.__add__, [ sorted([ i for i in names if i[0] == s ]) for s in symbols ] + [ sorted([ i for i in names if i[0] not in symbols])])
        self.orbit.event([self.user_key], ['names', [channel.lower(), names]])

    def joined(self, chan):
        self.orbit.event([self.user_key], ['joined', [self.nickname, chan.lower()]])

    def kickedFrom(self, chan, kicker, message):
        self.orbit.event([self.user_key], ['kickedFrom', [kicker.split('!',1)[0], chan.lower()]])

    def setNick(self, nickname):
        self.sendLine("NICK %s" % nickname)
        
    def irc_NICK(self, prefix, params):
        nick = prefix.split('!', 1)[0]
        if nick == self.nickname:
            self.nickChanged(params[0])
        else:
            self.userRenamed(nick, params[0])
        
    def nickChanged(self, nick):
        self.app.changeNick(self, nick)
        self.nickname = nick
        self.orbit.event([self.user_key], ['nickChanged', nick])
        self.user_key = '%s, 0, /chat' % nick
        
    def userRenamed(self, oldname, newname):
        self.orbit.event([self.user_key], ['userRenamed', [oldname, newname]])

    def userJoined(self, joiner, chan):
        self.orbit.event([self.user_key], ['userJoined', [joiner.split('!',1)[0], chan.lower()]])
        
    def userLeft(self, leaver, chan):
        self.orbit.event([self.user_key], ['userLeft', [leaver.split('!',1)[0], chan.lower(), 'has left']])
        
    def userKicked(self, leaver, chan, kicker, message):
        self.orbit.event([self.user_key], ['userLeft', [leaver.split('!',1)[0], chan.lower(),'has been kicked from']])
        
    def userQuit(self, leaver, quitMessage):
        self.orbit.event([self.user_key], ['userQuit', [leaver.split('!',1)[0], 'has quit OrbIRCt']])

    def signedOn(self):
        self.join(self.channel)
        reactor.callLater(PING_INTERVAL, self.send_ping)
        
    def connectionLost(self, *args, **kwargs):
        irc.IRCClient.connectionLost(self, *args, **kwargs)
        self.orbit.event([self.user_key], [ 'disconnect', ])
        self.app.irc_quit(self)
        
    def privmsg(self, sender, chan, msg):
        if chan == self.nickname:
            chan = sender.split('!',1)[0]
#        p = re.compile('\\x02|\\x16|\\x1f|\\x03(([0-9]{1,2})?(,[0-9]{1,2})?)?')
#        msg = p.sub('',msg)
        self.orbit.event([self.user_key], ['privmsg', [sender.split('!',1)[0], msg, chan.lower()]])
        
    def send_ping(self):
        if self.ping_count == PING_MISSED_MAX:
            self.quit(message='client timed out')
        else:
            self.orbit.event([self.user_key], [ 'ping', self.nickname ])
            self.ping_count += 1
            reactor.callLater(PING_INTERVAL, self.send_ping)
            
    def ping_reply(self):
        self.ping_count -=1

    def irc_RPL_NAMREPLY(self,prefix,params):  
        channel = params[2]
        users = params[3].split(' ')
        if self.name_reply is None:
            self.name_reply = (channel, [])
        self.name_reply[1].extend(users)
        
    def irc_RPL_ENDOFNAMES(self,prefix,params):
        name_reply = self.name_reply
        self.name_reply = None
        self.chan_names(*name_reply)

        
class RelayFactory(protocol.ClientFactory):
    protocol = RelayClient
    def __init__(self, nickname, app, user_key):
        self.nickname = nickname
        self.app = app
        self.user_key = user_key
        
    def buildProtocol(self, addr):
        p = self.protocol(self.nickname, self.app, self.user_key)
        self.client = p
        return p       