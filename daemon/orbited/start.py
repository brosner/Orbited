import os
import sys
import urlparse

from orbited import config
from orbited import logging

# NB: this is set after we load the configuration at "main".
logger = None

def _import(name):
    module_import = name.rsplit('.', 1)[0]
    return reduce(getattr, name.split('.')[1:], __import__(module_import))

def _setup_protocols(root):
    from twisted.internet import reactor
    protocols = [
        #child_path config_key  port_class_import,              factory_class_import
        ('tcp',     'proxy',    'orbited.cometsession.Port',    'orbited.proxy.ProxyFactory'),
    ]
    for child_path, config_key, port_class_import, factory_class_import in protocols:
        if config.map['[global]'].get('%s.enabled' % config_key) == '1':
            port_class = _import(port_class_import)
            factory_class = _import(factory_class_import)
            reactor.listenWith(port_class, factory=factory_class(), resource=root, childName=child_path)
            logger.info('%s protocol active' % config_key)

def _setup_static(root):
    from twisted.web import static
    for key, val in config.map['[static]'].items():
        if key == 'INDEX':
            key = ''
        if root.getStaticEntity(key):
            logger.error("cannot mount static directory with reserved name %s" % key)
            sys.exit(-1)
        root.putChild(key, static.File(val))

def main():
    # load configuration from configuration file and from command
    # line arguments.
    config.setup(sys.argv)

    logging.setup(config.map)

    # we can now safely get loggers.
    global logger; logger = logging.get_logger('orbited.start')

    # NB: we need to install the reactor before using twisted.
    reactor_name = config.map['[global]'].get('reactor')
    if reactor_name:
        install = _import('twisted.internet.%sreactor.install' % reactor_name)
        install()
        logger.info('using %s reactor' % reactor_name)

    from twisted.internet import reactor
    from twisted.web import resource
    from twisted.web import server
    from twisted.web import static

    root = resource.Resource()
    static_files = static.File(os.path.join(os.path.dirname(__file__), 'static'))
    root.putChild('static', static_files)
    site = server.Site(root)

    _setup_protocols(root)
    _setup_static(root)

    for addr in config.map['[listen]']:
        url = urlparse.urlparse(addr)
        hostname = url.hostname or ''
        if url.scheme == 'http':
            logger.info('Listening http@%s' % url.port)
            reactor.listenTCP(url.port, site, interface=hostname)
        elif url.scheme == 'https':
            from twisted.internet import ssl
            crt = config.map['[ssl]']['crt']
            key = config.map['[ssl]']['key']
            try:
                ssl_context = ssl.DefaultOpenSSLContextFactory(key, crt)
            except ImportError:
                raise
            except:
                logger.error("Error opening key or crt file: %s, %s" % (key, crt))
                sys.exit(-1)
            logger.info('Listening https@%s (%s, %s)' % (url.port, key, crt))
            reactor.listenSSL(url.port, site, ssl_context, interface=hostname)
        else:
            logger.error("Invalid Listen URI: %s" % addr)
            sys.exit(-1)

    reactor.run()

if __name__ == "__main__":
    main()
