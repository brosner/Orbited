# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


'''An example IRC log bot - logs a channel's events to a file.

If someone says the bot's name in the channel followed by a ':',
e.g.

  <foo> logbot: hello!

the bot will reply:

  <logbot> foo: I am a log bot

Run this script with two arguments, the channel name the bot should
connect to, and file to log to, e.g.:

  $ python ircLogBot.py test test.log

will log channel #test to the file 'test.log'.
'''


# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys

class BOT(irc.IRCClient):
    ''' A logging IRC bot. '''
    
    nickname = 'twistedbot'
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        print ('[connected at %s]' % time.asctime(time.localtime(time.time())))
    
    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        print ('[disconnected at %s]' % 
                        time.asctime(time.localtime(time.time())))
    # callbacks for events
    
    def signedOn(self):
        ''' Called when bot has succesfully signed on to server. '''
        self.telnet = self.factory.connected(self)
        self.join(self.factory.channel)
    
    def joined(self, channel):
        ''' This will get called when the bot joins the channel. '''
        self.telnet.sendLine('[I have joined %s]' % channel)
    
    def say(self, channel, message, length = None):
        if channel[0] not in '&#!+':
            channel = '#' + channel
        self.msg(channel, message, length)
        self.telnet.sendLine('||%s|| <%s> %s' % (channel, self.nickname, message))
    
    def noticed(self, user, channel, message):
        if hasattr(self, 'telnet'):
            user = user.split('!', 1)[0]
            self.telnet.sendLine('  --%s-- %s' % (user, message))
    
    def privmsg(self, user, channel, msg):
        '''This will get called when the bot receives a message.'''
        user = user.split('!', 1)[0]
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            theLine = '  **%s** %s' % (user, msg)
            #msg = 'It isn't nice to whisper!  Play nice with the group.'
            #self.msg(user, msg)
            #return
            
        else:
            theLine = '||%s|| <%s> %s' % (channel, user, msg)
        # Otherwise check to see if it is a message directed at me
        #if msg.startswith(self.nickname + ":"):
            #msg = "%s: I am a log bot" % user
            #self.msg(channel, msg)
            #print ("<%s> %s" % (self.nickname, msg))
            
        if hasattr(self, 'telnet'):
            self.telnet.sendLine(theLine)
    
    def leave(self, channel, reason=None):
        if channel[0] not in '&#!+': channel = '#' + channel
        if reason:
            self.sendLine('PART %s :%s' % (channel, reason))
            self.telnet.sendLine('PART %s :%s' % (channel, reason))
        else:
            self.sendLine('PART %s' % (channel,))
            self.telnet.sendLine('PART %s' % (channel,))
    
    def action(self, user, channel, msg):
        '''This will get called when the bot sees someone do an action.'''
        user = user.split('!', 1)[0]
        print ('* %s %s' % (user, msg))
    
    def notice(self, user, message):
        self.sendLine('NOTICE %s :%s' % (user, message))
        self.telnet.sendLine('You notice %s: %s' % (user, message))
    # irc callbacks
    
    def irc_NICK(self, prefix, params):
        '''Called when an IRC user changes their nickname.'''
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        print ('%s is now known as %s' % (old_nick, new_nick))
    

class BOTFactory(protocol.ClientFactory):
    ''' A factory for LogBots.
        
        A new protocol instance will be created each time we connect to
        the server.
    '''
    # the class of the protocol to build when new connection is made
    protocol = BOT
    
    def __init__(self, channel, filename, telnet):
        self.channel = channel
        self.filename = filename
        self.client = None
        self.telnet = telnet
    
    def buildProtocol(self): # FIXME: nothing here
        pass
    
    def connected(self, client):
        self.client = client
        return self.telnet
    
    def clientConnectionLost(self, connector, reason):
        ''' If we get disconnected, reconnect to server. '''
        connector.connect()
    
    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason
        reactor.stop()
    

if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)
    
    # create factory protocol and application
    f = BOTFactory(sys.argv[1], sys.argv[2])
    # connect factory to this host and port
    reactor.connectTCP('irc.perl.org', 6667, f)

    # run bot
    reactor.run()
