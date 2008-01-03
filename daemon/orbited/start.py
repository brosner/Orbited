#import psyco
#psyco.full()
import sys
import os
#sys.path.insert(0, os.path.abspath('.'))
from orbited import config
from orbited.app import Application
from orbited import transport
from orbited import plugin
from orbited.http import router

server = None

def main():
    load()
    do_start()

def load():
    global server
    # Config
    config_file = 'orbited.cfg'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    config.load(config_file)
    # Transports
    transport.load_transports()
    
    # Plugins
    plugin.load()
    
    # Setup Router
    router.setup()
    server = Application()
    
    
    
def do_start(): 
    global server  
    # Create Server
    
    # Start Server
    server.start()
    
    
def daemon():
    # Daemonize function for unix
    # modified from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
    # and redirect to null modified from:
    #    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/278731
    
    load()
    import os
    if (hasattr(os, "devnull")):
        REDIRECT_TO = os.devnull
    else:
        REDIRECT_TO = "/dev/null"
  
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit first parent
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 

    # do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent, print eventual PID before
            print "Daemon PID %d" % pid 
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1) 
        
#    import resource      # Resource usage information.
#    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
#    if (maxfd == resource.RLIM_INFINITY):
#        maxfd = MAXFD
  
   # Iterate through and close all file descriptors.
#    for fd in range(0, maxfd):
#        try:
#            os.close(fd)
#        except OSError:   # ERROR, fd wasn't open to begin with (ignored)
#            pass
    
    infd = sys.stdin.fileno()
    outfd = sys.stdout.fileno()
    errfd = sys.stderr.fileno()
    os.close(infd)
    os.close(outfd)
    os.close(errfd)
    os.open(REDIRECT_TO, os.O_RDWR)  # standard input (0)

    # Duplicate standard input to standard output and standard error.
    os.dup2(0, 1)            # standard output (1)
    os.dup2(0, 2)            # standard error (2)
        
        
    do_start()
    
def daemon2():
    from daemonize import createDaemon
    f = open('testdaemon', 'w')
    f.write('calling createDaemon\n')
    f.flush()
    createDaemon()
    f.write('called createDaemon\n')
    f.flush()
    import sys
    sys.stdout = f
    main()


if __name__ == '__main__':
    main()
