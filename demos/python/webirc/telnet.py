# Read username, output from non-empty factory, drop connections
# Use deferreds, to minimize synchronicity assumptions
# Write application. Save in 'finger.tpy'
from bot import *
from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic


class TelnetChatProtocol(basic.LineReceiver):
    def __init__(self, *args, **kwargs):
        self.irc = BOTFactory("#bigchannel", "none.log", self)
        reactor.connectTCP("irc.perl.org", 6667, self.irc) 
        
    def rawDataReceived(self, data):
        print "recieved data!: %s" % data
        return basic.LineReceiver.dataReceived(self, data)
        
    def lineReceived(self, line):    
        parsed = line.split(' ', 1)
        if len(parsed) == 1:
            command = parsed[0]
            data = ""
        else:
            command, data = parsed            
            self.process(command, data)        

    def process(self, command, data):
#        return self.transport.write("%s: %s\r\n" % (command, data))
        if self.irc.client is None:
            return self.sendLine("ERROR: still connecting")
        if command == "leave":
            if ' ' in data:
                channel, reason = data.split(' ',1)
                self.irc.client.leave(channel,reason)
            else:
                self.irc.client.leave(data)
        if command == "join":
            self.irc.client.join(data)
        if command == "say":
            i = data.find(' ')
            dest = data[:i]
            msg = data[i+1:]
            self.irc.client.say(dest, msg)
        if command == "msg":
            i = data.find(' ')
            dest = data[:i]
            msg = data[i+1:]
            self.irc.client.msg(dest, msg)
        if command == "notice":
            i = data.find(' ')
            dest = data[:i]
            msg = data[i+1:]
            self.irc.client.notice(dest, msg)

        
class TelnetChatFactory(protocol.ServerFactory):
    protocol = TelnetChatProtocol
    def __init__(self): 
        pass
    

application = service.Application('finger', uid=1, gid=1)
factory = TelnetChatFactory()
internet.TCPServer(79, factory).setServiceParent(
    service.IServiceCollection(application))