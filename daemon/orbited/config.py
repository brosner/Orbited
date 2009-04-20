import os
import sys

map = {
    '[global]': {
        'proxy.enabled': '1',
        'session.ping_interval': '30',
        'session.ping_timeout': '30'
    },

    '[logging]': {
        'debug': 'SCREEN',
        'info': 'SCREEN',
        'access': 'SCREEN',
        'warn': 'SCREEN',
        'error': 'SCREEN',
        'enabled.default': 'info,access,warn,error',
    },

    '[loggers]': {
        #'orbited.start': 'debug,info,access,warn,error',
    },

    '[listen]': [
        #'http://:8001',
    ],

    '[test]': {
        'stompdispatcher.enabled': '0',
    },

    '[ssl]': {
        #'key': 'orbited.key',
        #'crt': 'orbited.crt',
    },

    '[access]': {
        #('irc.freenode.net', 6667): ['localhost:8001', '127.0.0.1:8001'],
    },

    '[static]': {
        #'tmp': '/tmp',
    },

    'globalVars': {
        'monitoring': False,
        'connections': 0
    }
}

def config_error(msg):
    print "failed to load configuration file\n"
    print msg
    sys.exit(1)

def update(**kwargs):
    map.update(kwargs)
    return True

defaultPaths = [
    'orbited.cfg',
    os.path.join('/', 'etc', 'orbited.cfg'),
    os.path.join('/', 'Program Files', 'Orbited', 'etc', 'orbited.cfg'),
]

def setup(paths=defaultPaths, options={}):


    if not hasattr(options, 'config') or not options.config:
        # no config file specified, try to search it.
        for path in paths:
            if os.path.exists(path):
                options.config = path
                break

    if not hasattr(options, 'config') or not options.config:
        config_error('configuration file not found - please specify it in the --config command line argument')

    _load(open(options.config, 'r'))

def _load(f):
    # TODO why not use a python file as the configuration file?
    lines = [line.strip() for line in f.readlines()]
    map['default_config'] = 0    
    section = None
    try:
        for (i, line) in enumerate(lines):
            # ignore comments and empty lines.
            if '#' in line:
                line, comment = line.split('#', 1)
                line = line.strip()
            if not line:
                continue
            
            # start of new section; create a dictionary for it in map if one
            # doesn't already exist
            if line.startswith('[') and line.endswith(']'):
                section = line
                if section not in map:
                    map[section]  = {}
                continue
            
            # assign each source in the access section to a target address and port
            if section == '[access]':
                if '->' not in line:
                    raise Exception, 'line %s: "%s"\n[access] lines must contain an "->"'% ((i+1), line)
                source, dest = line.split('->')
                source, dest = source.strip(), dest.strip()
                if dest == "*":
                    raise Exception, 'line %s: "%s"\nillegal [access] entry: wildcard destination' % ((i+1), line)
                if ':' in dest:
                    daddr, dport = dest.split(':', 1)
                    dport = int(dport)
                else:
                    daddr, dport = dest, 80
                if (daddr, dport) not in map[section]:
                    map[section][(daddr, dport)] = []
                map[section][(daddr, dport)].append(source)
                continue
            if section == '[listen]':
                map[section].append(line)
                continue
            
            # skip lines which do not assign a value to a key
            if '=' not in line:
                raise Exception('parse error on line %d' % i)
            
            key, value = [side.strip() for side in line.split('=', 1)]
            
            # in log section, value should be a tuple of one or two values
            if section == '[log]':
                value = tuple([val.strip() for val in value.split(',', 1)])
            
            map[section][key] = value
    except Exception, e:
        config_error(e)
    return True
