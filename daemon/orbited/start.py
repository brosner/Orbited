import os
import sys
import urlparse
from orbited import __version__ as version
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

def _setup_static(root, config):
    from twisted.web import static
    for key, val in config['[static]'].items():
        if key == 'INDEX':
            key = ''
        if root.getStaticEntity(key):
            logger.error("cannot mount static directory with reserved name %s" % key)
            sys.exit(1)
        root.putChild(key, static.File(val))

def main():
    try:
        import twisted
    except ImportError:
        print "Orbited requires Twisted, which is not installed. See http://twistedmatrix.com/trac/ for installation instructions."
        sys.exit(1)
    import platform
    if platform.system() == "Windows":
        try:
            import win32api
        except ImportError:
            print "Orbited for Windows requires the Python for Windows Extensions, which are not installed. See http://python.net/crew/mhammond/win32/ for installation instructions."
            sys.exit(1)
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option(
        "-c",
        "--config",
        dest="config",
        default=None,
        help="path to configuration file"
    )
    parser.add_option(
        "-v",
        "--version",
        dest="version",
        action="store_true",
        default=False,
        help="print Orbited version"
    )
    parser.add_option(
        "-p",
        "--profile",
        dest="profile",
        action="store_true",
        default=False,
        help="run Orbited with a profiler"
    )
    parser.add_option(
        "-q",
        "--quickstart",
        dest="quickstart",
        action="store_true",
        default=False,
        help="run Orbited on port 8000 and MorbidQ on port 61613"
    )

    (options, args) = parser.parse_args()

    if args:
        print 'the "orbited" command does not accept positional arguments. type "orbited -h" for options.'
        sys.exit(1)

    if options.version:
        print "Orbited version: %s" % (version,)
        sys.exit(0)

    if options.quickstart:
        config.map['[listen]'].append('http://:8000')
        config.map['[listen]'].append('stomp://:61613')
        config.map['[access]'][('localhost',61613)] = ['*']
        print "Quickstarting Orbited"
    else:
        # load configuration from configuration
        # file and from command line arguments.
        config.setup(options=options)

    logging.setup(config.map)

    # we can now safely get loggers.
    global logger; logger = logging.get_logger('orbited.start')


    # NB: we need to install the reactor before using twisted.
    reactor_name = config.map['[global]'].get('reactor')
    if reactor_name:
        install = _import('twisted.internet.%sreactor.install' % reactor_name)
        install()
        logger.info('using %s reactor' % reactor_name)

    ############
    # This crude garbage corrects a bug in twisted
    #   Orbited ticket: http://orbited.org/ticket/111
    #   Twisted ticket: http://twistedmatrix.com/trac/ticket/2447
    import twisted.web.http
    twisted.web.http.HTTPChannel.setTimeout = lambda self, arg: None
    twisted.web.http.HTTPChannel.resetTimeout = lambda self: None
    ############

    from twisted.internet import reactor
    from twisted.web import resource
    from twisted.web import server
    from twisted.web import static
    import orbited.system

    root = resource.Resource()
    static_files = static.File(os.path.join(os.path.dirname(__file__), 'static'))
    root.putChild('static', static_files)
    root.putChild('system', orbited.system.SystemResource())
    
    if config.map['[test]']['stompdispatcher.enabled'] == '1':
        logger.info('stompdispatcher enabled')
    
    #static_files.putChild('orbited.swf', static.File(os.path.join(os.path.dirname(__file__), 'flash', 'orbited.swf')))
    site = server.Site(root)

    _setup_protocols(root)
    _setup_static(root, config.map)
    start_listening(site, config.map, logger)

    # switch uid and gid to configured user and group.
    if os.name == 'posix' and os.getuid() == 0:
        user = config.map['[global]'].get('user')
        group = config.map['[global]'].get('group')
        if user:
            import pwd
            import grp
            try:
                pw = pwd.getpwnam(user)
                uid = pw.pw_uid
                if group:
                    gr = grp.getgrnam(group)
                    gid = gr.gr_gid
                else:
                    gid = pw.pw_gid
                    gr = grp.getgrgid(gid)
                    group = gr.gr_name
            except Exception, e:
                logger.error('Aborting; Unknown user or group: %s' % e)
                sys.exit(1)
            logger.info('switching to user %s (uid=%d) and group %s (gid=%d)' % (user, uid, group, gid))
            os.setgid(gid)
            os.setuid(uid)
        else:
            logger.error('Aborting; You must define a user (and optionally a group) in the configuration file.')
            sys.exit(1)

    if options.profile:
        import hotshot
        prof = hotshot.Profile("orbited.profile")
        logger.info("running Orbited in profile mode")
        logger.info("for information on profiler, see http://orbited.org/wiki/Profiler")
        prof.runcall(reactor.run)
        prof.close()
    else:
        reactor.run()

def start_listening(site, config, logger):
    from twisted.internet import reactor
    from twisted.internet import protocol as protocol_module
    # allow stomp:// URIs to be parsed by urlparse
    urlparse.uses_netloc.append("stomp")
    # allow test server URIs to be parsed by urlparse
    from orbited.servers import test_servers
    for protocol in test_servers:
        urlparse.uses_netloc.append(protocol)

    for addr in config['[listen]']:
        if addr.startswith("stomp"):
            stompConfig = ""
            if " " in addr:
                addr, stompConfig = addr.split(" ",1)
        url = urlparse.urlparse(addr)
        hostname = url.hostname or ''
        if url.scheme == 'stomp':
            logger.info('Listening stomp@%s' % url.port)
            from morbid import get_stomp_factory
            morbid_instance = get_stomp_factory(stompConfig)
            config['morbid_instance'] = morbid_instance
            reactor.listenTCP(url.port, morbid_instance, interface=hostname)
        elif url.scheme == 'http':
            logger.info('Listening http@%s' % url.port)
            reactor.listenTCP(url.port, site, interface=hostname)
        elif url.scheme == 'https':
            from twisted.internet import ssl
            crt = config['[ssl]']['crt']
            key = config['[ssl]']['key']
            try:
                ssl_context = ssl.DefaultOpenSSLContextFactory(key, crt)
            except ImportError:
                raise
            except:
                logger.error("Error opening key or crt file: %s, %s" % (key, crt))
                sys.exit(1)
            logger.info('Listening https@%s (%s, %s)' % (url.port, key, crt))
            reactor.listenSSL(url.port, site, ssl_context, interface=hostname)
        elif url.scheme in test_servers:
            test_factory = protocol_module.ServerFactory()
            test_factory.protocol = test_servers[url.scheme]
            logger.info("Listening %s@%s"%(url.scheme, url.port))
            reactor.listenTCP(url.port, test_factory)
            if url.scheme == 'monitor':
                config['globalVars']['monitoring'] = url.port
        else:
            logger.error("Invalid Listen URI: %s" % addr)
            sys.exit(1)


if __name__ == "__main__":
    main()
