from datetime import datetime
import sys
import traceback

LOGTYPES = [ 'debug', 'access', 'warn', 'error', 'info' ]

_manager = None


def get_logger(name):
    return _manager.get_logger(name)

def setup(configmap):
    defaults = {}
    for logtype in LOGTYPES:
        defaults[logtype] = []        
        a = configmap['[logging]']
        b =a[logtype]
        outputs = b.split(',')
        for loc in outputs:
            loc = loc.strip()
            if not loc:
                continue
            if loc == 'enabled.default':
                continue
            if loc in ('SCREEN', 'STDOUT'):
                # NB: "SCREEN" is for backward compatability with 0.5-
                defaults[logtype].append(ScreenLog())
            elif loc == 'STDERR':
                defaults[logtype].append(ScreenLog(sys.stderr))
            else:
                defaults[logtype].append(FileLog(loc))
            defaults[logtype][-1].open()
    enabled = configmap['[logging]']['enabled.default'].split(',')
    overrides = {}
    for key, value in configmap['[loggers]'].items():
        overrides[key] = value.split(',')
    global _manager
    _manager = LoggerManager(enabled, defaults, overrides)
 

class LoggerManager(object):
 
    def __init__(self, enabled, defaults={}, overrides = {}):
        self.enabled = enabled
        self.defaults = defaults
        self.overrides = overrides
        self.loggers = {}
        
    def create_logger(self, name):
        defaults = {}
        if name in self.overrides:
            for key in self.overrides[name]:
                defaults[key] = self.defaults[key]
        else:
            for key in self.enabled:
                defaults[key] = self.defaults[key]
        return Logger(name, self.enabled, defaults)
        
    def get_logger(self, name):
        if name not in self.loggers:
            self.loggers[name] = self.create_logger(name)
        return self.loggers[name]
        
    def add_logger(self, name, logger):
        self.loggers[name] = logger
 

class Logger(object):
  
    def __init__(self, name, enabled, defaults):
        self.defaults = defaults
        self.name = name
        for key in LOGTYPES:
            if key not in defaults:
                setattr(self, key, self._empty)
 
    def _empty(self, *args, **kwargs):
        return
 
    def debug(self, *args, **kwargs):
        date = "[]"
        now = datetime.now()
        date = now.strftime("%m/%d/%y %H:%M:%S:") + str(now.microsecond)[:3]
        output = date + ' ' + 'DEBUG  ' + self.name + "\t" + "".join([str(i) for i in args]) + '\n'
        
        if kwargs.get('tb', False):
            exception, instance, tb = traceback.sys.exc_info()
            output += "".join(traceback.format_tb(tb))
        if kwargs.get('stack', False):
            output += "".join(traceback.format_stack()[:-1])

        for logger in self.defaults['debug']:
            logger.log(output)
 
    def access(self, item, *args, **kwargs):
        date = "[]"
        now = datetime.now()
        date = now.strftime("%m/%d/%y %H:%M:%S:") + str(now.microsecond)[:3]
        output = date + ' ' + 'ACCESS ' + item + "\t" + "".join([str(i) for i in args]) + '\n'
        
        if kwargs.get('tb', False):
            exception, instance, tb = traceback.sys.exc_info()
            output += "".join(traceback.format_tb(tb))
        if kwargs.get('stack', False):
            output += "".join(traceback.format_stack()[:-1])
        
        for logger in self.defaults['access']:
            logger.log(output)
      
    def warn(self, *args, **kwargs):
        now = datetime.now()
        date = "[]"
        now = datetime.now()
        date = now.strftime("%m/%d/%y %H:%M:%S:") + str(now.microsecond)[:3]
        output = date + ' ' + 'WARN   ' + self.name + "\t" + "".join([str(i) for i in args]) + '\n'
        
        if kwargs.get('tb', False):
            exception, instance, tb = traceback.sys.exc_info()
            output += "".join(traceback.format_tb(tb))
        if kwargs.get('stack', False):
            output += "".join(traceback.format_stack()[:-1])
        
        for logger in self.defaults['warn']:
            logger.log(output)
      
    def info(self, *args, **kwargs):
        date = "[]"
        now = datetime.now()
        date = now.strftime("%m/%d/%y %H:%M:%S:") + str(now.microsecond)[:3]
        output = date + ' ' + 'INFO   ' + self.name + "\t" + "".join([str(i) for i in args]) + '\n'
        
        if kwargs.get('tb', False):
            exception, instance, tb = traceback.sys.exc_info()
            output += "".join(traceback.format_tb(tb))
        if kwargs.get('stack', False):
            output += "".join(traceback.format_stack()[:-1])
        
        for logger in self.defaults['info']:
            logger.log(output)
 
    def error(self, *args, **kwargs):
        date = "[]"
        now = datetime.now()
        date = now.strftime("%m/%d/%y %H:%M:%S:") + str(now.microsecond)[:3]
        output = date + ' ' + 'ERROR  ' + self.name + "\t" + "".join([str(i) for i in args]) + '\n'
        
        if kwargs.get('tb', False):
            exception, instance, tb = traceback.sys.exc_info()
            output += "".join(traceback.format_tb(tb))
            self.debug(output)
        if kwargs.get('stack', False):
            output += "".join(traceback.format_stack()[:-1])
        
        for logger in self.defaults['error']:
            logger.log(output)


class ScreenLog(object):

    def __init__(self, file=sys.stdout):
        self.enabled = True
        self.file = file

    def log(self, data):
        if not self.enabled:
            return
        # Something weird was happening with the daemonization stuff
        # that made this just break.
        try:
            self.file.write(data)
        except:
            self.enabled = False

    def open(self):
        pass

    def flush(self):
        pass

    def close(self):
        pass
    
    
class FileLog(object):

    def __init__(self, filename):
        self.filename = filename
        self.f = None
    
    def log(self, data):
        self.f.write(data)

    def open(self):
        self.f = open(self.filename, 'a')
    
    def flush(self):
        self.f.flush()
    
    def close(self):
        self.f.close()

