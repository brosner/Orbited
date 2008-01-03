import os
import event
import util
from orbited import plugin
from orbited.log import getLogger

logger = getLogger('Admin')

class AdminPlugin(plugin.Plugin):
    name = 'admin'
    event_path = "/_/admin/event"
    static = os.path.join(os.path.split(__file__)[0], 'static')

    def __init__(self):
        self.data = {'plugins':{},'sessions':{}}
        event.timeout(1,self.send)

    def init_data(self):
        return {'bandwidth':0,'msgs':0,'users':0}

    def add_location(self,type,location):
        if location not in self.data[type]:
            self.data[type][location] = self.init_data()
        self.data[type][location]['users'] += 1

    def remove_location(self,type,location):
        if location not in self.data[type]:
            print '[error] close_orbited_connection: %s not in self.data[%s]' % (location,type)
            return
        self.data[type][location]['users'] -= 1

    def accept_orbited_connection(self,conn):
        user,session,location = conn.key
        if location[:3] == '/_/':
            self.add_location('plugins',location[3:-6])
        else:
            self.add_location('sessions',location)

    def close_orbited_connection(self,conn):
        user,session,location = conn.key
        if location[:3] == '/_/':
            self.remove_location('plugins',location[3:-6])
        else:
            self.remove_location('sessions',location)

    def add_bandwidth(self,type,location,amount):
        if location not in self.data[type]:
            print '[error] bandwidth_monitor: %s not in self.data[%s]' % (location,type)
            return
        self.data[type][location]['bandwidth'] += amount
        self.data[type][location]['msgs'] += 1

    @plugin.hook(">http.http.HTTPConnection.sent_amount")
    def bandwidth_monitor(self, conn, amount):
        if conn.state == 'orbited':
            location = conn.browser_conn.location
            if location[:3] == '/_/':
                self.add_bandwidth('plugins',location[3:-6],amount)
            else:
                self.add_bandwidth('sessions',location,amount)

    def clear_data(self):
        for type in self.data:
            for location in self.data[type]:
                self.data[type][location]['bandwidth'] = 0
                self.data[type][location]['msgs'] = 0

    def update_data(self):
        pass

    def send(self):
        self.update_data()
        self.broadcast()
        self.clear_data()
        return True
