import logging
from config import map as config
from datetime import datetime

loggers = {
    'LOG': logging.getLogger('LOG'),
    'ACCESS': logging.getLogger('ACCESS')
}
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
access_formatter = logging.Formatter('%(asctime)s %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)
access_console = logging.StreamHandler()
access_console.setLevel(logging.DEBUG)
access_console.setFormatter(access_formatter)
loggers['LOG'].setLevel(getattr(logging, config['[log]']['level']))
loggers['LOG'].addHandler(console)
loggers['ACCESS'].setLevel(getattr(logging, config['[log]']['level']))
loggers['ACCESS'].addHandler(access_console)

def loggo(*args, **kwargs):
    print args, kwargs

class Loggo(object):
    def __getattr__(self, name):
        return loggo
    
    ACCESS = loggo
    INFO = loggo
    DEBUG = loggo
    WARN = loggo
    CRITICAL = loggo

jk = Loggo()
def getLogger(name):
#    return jk
    loggers['LOG'].debug('getLogger(%s) called' % name)
    if not name in loggers:
        loggers['LOG'].debug('creating logger %s' % name)
        loggers[name] = logging.getLogger(name)
        configure(name)
    return loggers[name]

#getLogger = logging.getLogger

def configure(name):
    loggers['LOG'].debug('Configuring logger %s' % name)
    logger = loggers[name]
    logger.setLevel(getattr(logging, config['[log]']['level']))
    logger.addHandler(console)
