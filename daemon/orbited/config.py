map = {
    '[global]': {
        'op.port': '9000',
        'http.port': '8000',
        'admin.enabled': '0',
        'proxy.enabled': '1',
        'proxy.keepalive': '1',
        'proxy.keepalive_default_timeout': 300,
        'log.enabled': '1',
        'session.default_key': '0', # TODO: change to token.default_key
        'session.timeout': 5,
        'event.retry_limit': 1
    },
    '[transport]': {
        'default': 'stream',
        'xhr.timeout': '30',
    },
    '[admin]': {
        'admin.port': '9001'
    },
    '[proxy]': [
        # ('/', ('69.60.117.172', 80)),
        # ('/', ('ORBITED', None)),
    ],
    '[log]': {
        'type': 'basic',
        'level': 'INFO',
        # 'type': 'file',
        # 'location': 'logging.conf'
        # 'log.access': ('screen',),
        # 'log.error': ('screen',),
        # 'log.event': ('screen',)
    },
    'default_config': 1, # set to 0 later if we load a config file
}

def update(**kwargs):
    map.update(kwargs)
    return True

def load(filename):
    try:
        f = open(filename)
        lines = [line.strip() for line in f.readlines()]
        map['default_config'] = 0
    
    except IOError:    
        print filename, 'could not be found. Using default configuration'
        return False
        # lines = default.split('\n')
    
    section = None
    for line in lines:
        
        # ignore comments
        if '#' in line:
            line, comment = line.split('#', 1)
        if not line:
            continue
        
        # start of new section; create a dictionary for it in map if one
        # doesn't already exist
        if line.startswith('[') and line.endswith(']'):
            section = line
            if section not in map:
                map[section]  = {}
            continue
        
        # assign each source in the proxy section to a target address and port
        if section == '[proxy]':
            source, target = [side.strip() for side in line.split('->')]
            if target.startswith('http://'):
                target = target[7:]
            if ':' in target:
                addr, port = target.split(':', 1)
                port = int(port)
            else:
                addr, port = target, 80
            map[section].append((source, (addr, port)))
            continue
        
        # skip lines which do not assign a value to a key
        if '=' not in line:
            continue
        
        key, value = [side.strip() for side in line.split('=', 1)]
        
        # in log section, value should be a tuple of one or two values
        if section == '[log]':
            value = tuple([val.strip() for val in value.split(',', 1)])
        
        map[section][key] = value
    
    print 'CONFIG'
    print map
    return True
